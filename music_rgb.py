"""Music RGB application entry point and packaged-app diagnostics."""
import argparse
import ctypes
import json
import logging
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox

from asus_keyboard import AsusKeyboard
from effects import ReactiveColor
from interface import App
from keyboard_backends import compatibility_report
from settings import settings_path


def diagnose():
    compatibility = compatibility_report()
    result = {"devices": App.get_devices(), "keyboard_compatibility": compatibility}
    if compatibility.get("backend") == "asus-atkacpi":
        keyboard = AsusKeyboard()
        try:
            result["keyboard"] = keyboard.probe()
        finally:
            keyboard.close()
    else:
        result["keyboard"] = {"probe": "not attempted", "reason": compatibility["note"]}
    return result


def smoke_test(path):
    import time
    root = tk.Tk()
    root.withdraw()
    app = App(root, tray=True)
    app.vars["preview"].set(True)
    app.start()
    start = time.monotonic()
    while time.monotonic()-start < 3:
        root.update()
        time.sleep(.02)
    report = {"packaged": bool(getattr(sys, "frozen", False)),
              "devices": len(app.devices), "live_frame": app.session.latest is not None,
              "error": app.last_error, "tray_created": app.tray is not None,
              "controls": list(app.vars), "mode": app.vars["mode"].get()}
    app.stop()
    deadline = time.monotonic()+4
    while app.session.running and time.monotonic() < deadline:
        root.update()
        time.sleep(.02)
    report["worker_stopped"] = not app.session.running
    if app.tray:
        app.tray.stop()
    root.destroy()
    Path(path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["live_frame"] and report["worker_stopped"] and not report["error"] else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnose", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--smoke-test-report", type=Path)
    args = parser.parse_args()
    if args.smoke_test_report:
        return smoke_test(args.smoke_test_report)
    if args.diagnose:
        result = json.dumps(diagnose(), indent=2)
        if args.report:
            args.report.write_text(result, encoding="utf-8")
        elif sys.stdout:
            print(result)
        return 0
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    api.CreateMutexW.restype = ctypes.c_void_p
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    mutex = api.CreateMutexW(None, False, "Local\\MusicRGBImmersive")
    exists = ctypes.get_last_error() == 183
    if exists:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Music RGB", "Music RGB is already running. Open it from the icon beside the clock.")
        root.destroy()
        if mutex:
            api.CloseHandle(mutex)
        return 0
    try:
        root = tk.Tk()
        app = App(root)
        def callback_error(kind, value, trace):
            logging.error("UI callback error", exc_info=(kind, value, trace))
            messagebox.showerror("Music RGB", str(value), parent=root)
        root.report_callback_exception = callback_error
        root.mainloop()
    finally:
        if mutex:
            api.CloseHandle(mutex)
    return 0


if __name__ == "__main__":
    folder = settings_path().parent
    folder.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=folder / "music_rgb.log", level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        raise SystemExit(main())
    except Exception:
        logging.exception("Application failure")
        raise

"""Restricted ASUS keyboard lighting interface; no fan/power controls.

Protocol reference: https://github.com/seerge/g-helper/blob/main/app/AsusACPI.cs
"""
import ctypes
from ctypes import wintypes
import os
import struct


def laptop_profile():
    """Return the local ASUS model and its known keyboard lighting type."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\BIOS") as key:
            model = winreg.QueryValueEx(key, "SystemProductName")[0]
    except OSError:
        model = "Unknown ASUS laptop"
    if "X1605VA" in model.upper():
        return model, "vivobook-white"
    upper = model.upper()
    # These TUF families use ASUS's model-specific ATKACPI keyboard RGB
    # endpoints documented by the G-Helper ACPI implementation. Regional SKU
    # differences still require the read-only endpoint probe below to pass.
    if any(family in upper for family in (
            "FA506", "FA507", "FA608", "FA706", "FX506", "FX507", "FX607")):
        return model, "tuf-rgb"
    return model, "unknown"


class AsusKeyboard:
    def __init__(self):
        if os.name != "nt":
            raise RuntimeError("This controller requires Windows.")
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
            wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
            wintypes.HANDLE]
        self.api.CreateFileW.restype = wintypes.HANDLE
        self.api.DeviceIoControl.argtypes = [wintypes.HANDLE, wintypes.DWORD,
            ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
        self.api.DeviceIoControl.restype = wintypes.BOOL
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.api.CloseHandle.restype = wintypes.BOOL
        self.handle = self.api.CreateFileW(r"\\.\ATKACPI", 0xC0000000,
                                           3, None, 3, 0x80, None)
        if self.handle == ctypes.c_void_p(-1).value:
            self.handle = None
            error = ctypes.get_last_error()
            if error == 5:
                raise PermissionError("ASUS driver access denied. Run Launch.cmd as administrator.")
            raise ctypes.WinError(error)
        self.endpoint = None
        self.previous = None
        self.previous_brightness = None
        self.model, self.profile = laptop_profile()

    def _call(self, method, args):
        packet = struct.pack("<II", method, len(args)) + args
        source = ctypes.create_string_buffer(packet)
        dest = ctypes.create_string_buffer(16)
        returned = wintypes.DWORD()
        if not self.api.DeviceIoControl(self.handle, 0x0022240C, source,
                len(packet), dest, len(dest), ctypes.byref(returned), None):
            raise ctypes.WinError(ctypes.get_last_error())
        if returned.value < 4:
            raise RuntimeError("ASUS driver returned an incomplete response.")
        return struct.unpack_from("<I", dest.raw)[0]

    def probe(self):
        """Read-only status queries for the two known keyboard endpoints."""
        statuses = {"model": self.model, "profile": self.profile}
        for dev in (0x00100056, 0x0010005A):
            try:
                statuses[hex(dev)] = hex(self._call(0x53545344, struct.pack("<II", dev, 0)))
            except OSError as exc:
                statuses[hex(dev)] = str(exc)
        try:
            statuses["keyboard_brightness"] = hex(self._call(
                0x53545344, struct.pack("<II", 0x00050021, 0)))
        except OSError as exc:
            statuses["keyboard_brightness"] = str(exc)
        return statuses

    def _supported_rgb_endpoints(self):
        """Read-only ASUS DSTS support check, following G-Helper's convention."""
        supported = []
        for dev in (0x00100056, 0x0010005A):
            try:
                raw = self._call(0x53545344, struct.pack("<II", dev, 0))
                # G-Helper decodes DeviceGet as returned_value - 0x10000 and
                # considers a non-negative result a supported endpoint.
                if raw >= 0x10000:
                    supported.append(dev)
            except OSError:
                continue
        return supported

    def set_color(self, rgb):
        rgb = tuple(max(0, min(255, int(v))) for v in rgb)
        if len(rgb) != 3:
            raise ValueError("Expected three RGB components.")
        if self.profile == "vivobook-white":
            # The X1605VA has a white backlight with three lit steps, not RGB.
            # Preserve the effect's value independently of its hue: luminance
            # made saturated colors look artificially dim and collapsed most
            # output into the first two firmware levels. A gentle perceptual
            # curve makes the limited hardware range more useful at low levels.
            intensity = max(rgb) / 255
            self.set_brightness(round((intensity ** 0.55) * 3))
            return
        if self.profile == "unknown":
            raise RuntimeError(
                f"Unsupported ASUS keyboard model: {self.model}. "
                "This build supports the Vivobook X1605VA and TUF FA706.")
        if rgb == self.previous:
            return
        def send(dev, opcode):
            payload = struct.pack("<I", dev) + bytes((opcode, 0, *rgb, 0))
            return self._call(0x53564544, payload)
        if self.endpoint == 0x00100056:
            result = send(self.endpoint, 0xB4)
        elif self.endpoint == 0x0010005A:
            send(self.endpoint, 0xB3)
            result = send(self.endpoint, 0xB4)
        else:
            supported = self._supported_rgb_endpoints()
            if not supported:
                raise RuntimeError(
                    f"No supported ASUS RGB keyboard endpoint was found for {self.model}. "
                    "No lighting command was sent.")
            self.endpoint = supported[0]
            if self.endpoint == 0x0010005A:
                send(self.endpoint, 0xB3)
            result = send(self.endpoint, 0xB4)
        if result != 1:
            raise RuntimeError(f"ASUS keyboard rejected the colour command (0x{result:X}).")
        self.previous = rgb

    def set_brightness(self, level):
        """Set the X1605VA white keyboard backlight to one of four levels."""
        level = max(0, min(3, int(level)))
        if level == self.previous_brightness:
            return
        result = self._call(0x53564544,
            struct.pack("<II", 0x00050021, 0x80 | level))
        if result != 1:
            raise RuntimeError(
                "ASUS rejected the keyboard brightness command. "
                "Check that ASUS System Control Interface is installed.")
        self.previous_brightness = level

    def close(self):
        if self.handle is not None:
            self.api.CloseHandle(self.handle)
            self.handle = None

"""Tk control panel. All Tk calls stay on its main thread."""
import json
import queue
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from audio_session import AudioSession, get_devices
from keyboard_backends import discover_keyboard
from asus_keyboard import laptop_profile
from effects import MODES, PALETTES
import settings

BG = "#0d1019"
PANEL = "#171c2b"
TEXT = "#eef0fb"
MUTED = "#a4acc4"
ACCENT = "#b29aff"


class App:
    get_devices = staticmethod(get_devices)

    def __init__(self, root, tray=True):
        self.root = root
        self.keyboard_info = discover_keyboard()
        self.laptop_model = self.keyboard_info.model
        _, self.keyboard_profile = laptop_profile()
        self.closing = False
        self.tray = None
        self.events = queue.Queue()
        self.session = AudioSession(self.events)
        self.devices = {}
        self.last_error = None
        self.values = settings.load()
        self.vars = {}
        for key, value in self.values.items():
            kind = tk.BooleanVar if isinstance(value, bool) else tk.DoubleVar if isinstance(value, float) else tk.StringVar
            self.vars[key] = kind(value=value)
        root.title("Music RGB | Immersive")
        root.geometry("920x920")
        root.minsize(840, 900)
        root.configure(bg=BG)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Title.TLabel", font=("Segoe UI", 25, "bold"))
        style.configure("TButton", background=PANEL, foreground=TEXT, padding=(12, 7), borderwidth=0)
        style.map("TButton", background=[("active", "#343050"), ("disabled", PANEL)])
        style.configure("TCombobox", fieldbackground=PANEL, background=PANEL, foreground=TEXT,
                        arrowcolor=ACCENT, padding=6)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", TEXT)])
        style.configure("TCheckbutton", background=BG, foreground=TEXT)
        style.map("TCheckbutton", background=[("active", BG)])
        style.configure("Horizontal.TScale", background=BG, troughcolor=PANEL)
        root.option_add("*TCombobox*Listbox.background", PANEL)
        root.option_add("*TCombobox*Listbox.foreground", TEXT)
        box = ttk.Frame(root, padding=24)
        box.pack(fill="both", expand=True)
        header = ttk.Frame(box)
        header.pack(fill="x")
        ttk.Label(header, text="Music RGB", style="Title.TLabel").pack(side="left")
        device_label = f'{self.keyboard_info.manufacturer}  /  {self.laptop_model}  /  {self.keyboard_info.lighting.upper()}'
        ttk.Label(header, text=device_label, foreground=ACCENT).pack(side="right")
        tagline = ("Your music controls the white keyboard backlight's intensity."
                   if self.keyboard_profile == "vivobook-white"
                   else "Audio-reactive lighting with hardware support reported conservatively.")
        ttk.Label(box, text=tagline,
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 12))
        ttk.Label(box, text=self.keyboard_info.note or self.keyboard_info.status,
                  style="Muted.TLabel", wraplength=860).pack(anchor="w", pady=(0, 8))
        if self.keyboard_profile == "vivobook-white":
            ttk.Label(box, text="The white backlight changes uniformly through three steps plus off. Music wave's per-key pattern is preview-only.",
                      style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        self.canvas = tk.Canvas(box, height=125, bg=PANEL, highlightthickness=0)
        self.canvas.pack(fill="x", pady=(0, 8))
        self.live = tk.StringVar(value="Ready when you are")
        ttk.Label(box, textvariable=self.live, foreground=ACCENT).pack(anchor="w")
        source_row = ttk.Frame(box)
        source_row.pack(fill="x", pady=(8, 2))
        ttk.Label(source_row, text="Audio source").pack(side="left", padx=(0, 10))
        self.source_box = ttk.Combobox(source_row, textvariable=self.vars["audio_source"],
            values=("Playback output", "Microphone input"), state="readonly", width=24)
        self.source_box.pack(side="left")
        self.source_box.bind("<<ComboboxSelected>>", self.refresh)
        ttk.Label(source_row, text="Microphone input is processed locally while sync is active.",
            style="Muted.TLabel").pack(side="left", padx=10)
        output = ttk.Frame(box)
        output.pack(fill="x", pady=10)
        self.device_box = ttk.Combobox(output, textvariable=self.vars["device"], state="readonly")
        self.device_box.pack(side="left", fill="x", expand=True)
        self.refresh_button = ttk.Button(output, text="Refresh outputs", command=self.refresh)
        self.refresh_button.pack(side="right", padx=(8, 0))
        body = ttk.Frame(box)
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 22))
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)
        self.combo(left, "Effect", "mode", MODES)
        palette_label = ("Preview colour palette" if self.keyboard_profile == "vivobook-white"
                         else "Colour palette (Bass pulse, Beat bloom, Aurora)")
        self.combo(left, palette_label, "palette", list(PALETTES))
        self.color_button = ttk.Button(left, text="Choose custom colour", command=self.choose_color)
        self.color_button.pack(fill="x", pady=(4, 10))
        ttk.Label(left, text="Presets").pack(anchor="w")
        self.preset = tk.StringVar(value="Song vibe")
        preset_box = ttk.Combobox(left, textvariable=self.preset, values=list(settings.PRESETS), state="readonly")
        preset_box.pack(fill="x", pady=4)
        preset_box.bind("<<ComboboxSelected>>", self.apply_preset)
        actions = ttk.Frame(left)
        actions.pack(fill="x")
        ttk.Button(actions, text="Save preset...", command=self.export_preset).pack(side="left", fill="x", expand=True)
        ttk.Button(actions, text="Load...", command=self.import_preset).pack(side="left", padx=(6, 0))
        self.combo(left, "When sync stops", "stop_color", ["Light blue", "White", "Dim purple", "Off", "Keep last", "Custom colour"])
        ttk.Checkbutton(left, text="Preview only", variable=self.vars["preview"]).pack(anchor="w", pady=3)
        ttk.Checkbutton(left, text="Keep window on top", variable=self.vars["topmost"],
                        command=self.set_topmost).pack(anchor="w", pady=3)
        for title, key, low, high in (("Sensitivity", "gain", .2, 4),
                ("Brightness", "brightness", 0, 1), ("Smoothness", "smoothing", 0, 1),
                ("Animation speed", "speed", .2, 3), ("Silence threshold", "noise_floor", 0, .02),
                ("Glow during silence", "idle", 0, .3)):
            row = ttk.Frame(right)
            row.pack(fill="x", pady=(0, 2))
            ttk.Label(row, text=title).pack(side="left")
            value_label = ttk.Label(row, foreground=MUTED)
            value_label.pack(side="right")
            def update(*_, k=key, label=value_label):
                label.configure(text=f"{self.vars[k].get():.3f}" if k == "noise_floor" else f"{self.vars[k].get():.2f}")
            self.vars[key].trace_add("write", update)
            update()
            ttk.Scale(right, variable=self.vars[key], from_=low, to=high).pack(fill="x", pady=(0, 8))
        buttons = ttk.Frame(box)
        buttons.pack(fill="x", pady=(10, 5))
        self.start_button = ttk.Button(buttons, text="Start sync", command=self.start)
        self.start_button.pack(side="left")
        ttk.Button(buttons, text="Stop", command=self.stop).pack(side="left", padx=8)
        self.tray_button = ttk.Button(buttons, text="Hide to tray", command=self.hide)
        self.tray_button.pack(side="left")
        ttk.Button(buttons, text="Save settings", command=self.save_settings).pack(side="right")
        self.status = tk.StringVar(value="Audio stays on this PC. Set keyboard brightness above zero.")
        ttk.Label(box, textvariable=self.status, style="Muted.TLabel", wraplength=860).pack(anchor="w", pady=5)
        ttk.Label(box, text="Song vibe estimates energy and tone over several seconds. It does not read lyrics or song metadata.",
                  style="Muted.TLabel", wraplength=860).pack(anchor="w")
        self.refresh()
        self.set_topmost()
        if tray:
            self.setup_tray()
        else:
            self.tray_button.configure(state="disabled")
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(50, self.tick)

    def combo(self, parent, title, key, values):
        ttk.Label(parent, text=title).pack(anchor="w", pady=(5, 0))
        ttk.Combobox(parent, textvariable=self.vars[key], values=values, state="readonly").pack(fill="x", pady=(4, 8))

    def refresh(self):
        if self.session.running:
            return
        try:
            self.devices = get_devices(self.vars["audio_source"].get())
            self.device_box.configure(values=list(self.devices))
            if self.vars["device"].get() not in self.devices:
                self.vars["device"].set(next(iter(self.devices), ""))
        except Exception as exc:
            self.status.set("Unable to list outputs: " + str(exc))

    def options(self):
        return settings.validate({k: v.get() for k, v in self.vars.items()})

    def start(self):
        if self.closing or self.session.running:
            return
        device = self.devices.get(self.vars["device"].get())
        if device is None:
            self.status.set("Select an audio device, then use Refresh outputs.")
            return
        if not self.vars["preview"].get() and not self.keyboard_info.backend:
            self.status.set("Keyboard lighting control is not supported for this detected model yet. Turn on Preview only to test the audio visualizer.")
            return
        self.last_error = None
        self.start_button.configure(state="disabled")
        self.device_box.configure(state="disabled")
        self.refresh_button.configure(state="disabled")
        self.source_box.configure(state="disabled")
        self.status.set("Connecting to " + self.vars["audio_source"].get().lower() + "...")
        self.session.start(device, self.options())

    def stop(self):
        self.session.stop()
        if self.session.running:
            self.status.set("Stopping...")

    def choose_color(self):
        _, color = colorchooser.askcolor(color=self.vars["custom"].get(), parent=self.root)
        if color:
            self.vars["custom"].set(color)
            self.vars["mode"].set("Custom colour")

    def apply_preset(self, *_):
        for key, value in settings.PRESETS.get(self.preset.get(), {}).items():
            self.vars[key].set(value)

    def export_preset(self):
        path = filedialog.asksaveasfilename(parent=self.root, title="Save lighting preset",
            defaultextension=".json", initialfile="My music preset.json", filetypes=[("Lighting preset", "*.json")])
        if path:
            try:
                settings.save(self.options(), settings.Path(path))
                self.status.set("Preset saved.")
            except OSError as exc:
                messagebox.showerror("Cannot save preset", str(exc), parent=self.root)

    def import_preset(self):
        path = filedialog.askopenfilename(parent=self.root, title="Load lighting preset", filetypes=[("Lighting preset", "*.json")])
        if path:
            try:
                with open(path, encoding="utf-8") as handle:
                    raw = json.load(handle)
                if not isinstance(raw, dict) or "mode" not in raw:
                    raise ValueError("This is not a lighting preset.")
                values = settings.validate(raw)
                for key, value in values.items():
                    if key not in ("device", "topmost", "preview"):
                        self.vars[key].set(value)
                self.preset.set("Loaded preset")
                self.status.set("Preset loaded.")
            except (OSError, ValueError) as exc:
                messagebox.showerror("Cannot load preset", str(exc), parent=self.root)

    def save_settings(self):
        try:
            settings.save(self.options())
            self.status.set("Settings saved for your next session.")
        except OSError as exc:
            self.status.set("Could not save settings: " + str(exc))

    def set_topmost(self):
        self.root.attributes("-topmost", self.vars["topmost"].get())

    def setup_tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
            image = Image.new("RGB", (64, 64), BG)
            draw = ImageDraw.Draw(image)
            for x, h in ((10, 20), (22, 38), (34, 48), (46, 30)):
                draw.rounded_rectangle((x, 54-h, x+7, 54), radius=3, fill=ACCENT)
            def command(name):
                return lambda icon, item: self.events.put(("command", name))
            self.tray = pystray.Icon("MusicRGB", image, "Music RGB", pystray.Menu(
                pystray.MenuItem("Show controls", command("show"), default=True),
                pystray.MenuItem("Start / resume", command("start")),
                pystray.MenuItem("Stop", command("stop")),
                pystray.MenuItem("Quit", command("quit"))))
            self.tray.run_detached()
        except Exception as exc:
            self.tray = None
            self.tray_button.configure(state="disabled")
            self.status.set("Tray unavailable; use the window controls. " + str(exc))

    def hide(self):
        if self.tray:
            self.root.withdraw()

    def show(self):
        self.root.deiconify()
        self.root.lift()

    def draw(self, frame):
        canvas = self.canvas
        canvas.delete("all")
        width = max(400, canvas.winfo_width())
        rgb = frame["rgb"]
        if self.keyboard_profile == "vivobook-white":
            intensity = max(rgb) / 255
            level = round((intensity ** 0.55) * 3)
            gray = round(level * 255 / 3)
            rgb = (gray, gray, gray)
        color = "#{:02x}{:02x}{:02x}".format(*rgb)
        canvas.create_rectangle(0, 0, width, 7, fill=color, outline="")
        wave_mode = (self.vars["mode"].get() == "Music wave" and
                     "wave_levels" in frame and "wave_rgb" in frame)
        for row in range(4):
            for col in range(14):
                x = 18+col*21
                y = 23+row*21
                key_color = color
                if wave_mode:
                    if self.keyboard_profile == "vivobook-white":
                        intensity = max(0.0, min(1.0, float(frame["wave_levels"][col])))
                        step = round((intensity ** 0.55) * 3)
                        shade = round(step * 255 / 3)
                        key_color = "#{:02x}{:02x}{:02x}".format(shade, shade, shade)
                    else:
                        key_rgb = frame["wave_rgb"][col]
                        key_color = "#{:02x}{:02x}{:02x}".format(*(int(c) for c in key_rgb))
                canvas.create_rectangle(x, y, x+17, y+16, fill=key_color, outline="#36334d")
        gap = (width-350)/18
        for i, height in enumerate(frame["bars"]):
            x = 330+i*gap
            canvas.create_rectangle(x, 110-max(2, float(height)*85), x+max(3, gap-5), 110,
                                    fill=ACCENT, outline="")
        text = f'{self.vars["mode"].get()}  /  {round(frame["level"]*100)}% energy'
        if self.keyboard_profile == "vivobook-white":
            text += "  /  white backlight intensity"
            if wave_mode:
                text += "  /  moving per-key wave shown in preview only"
        if self.vars["mode"].get() == "Song vibe":
            text += "  /  " + frame["vibe"]
        if wave_mode:
            text += "  /  spatial wave in preview; hardware output follows overall level"
        if self.vars["preview"].get():
            text += "  /  Preview only"
        self.live.set(text)

    def tick(self):
        self.session.options = self.options()
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind in ("status", "error"):
                if kind == "error":
                    self.last_error = value
                self.status.set(value)
            elif kind == "done":
                self.start_button.configure(state="normal")
                self.device_box.configure(state="readonly")
                self.refresh_button.configure(state="normal")
                self.source_box.configure(state="readonly")
                self.status.set(self.last_error or "Stopped. Ready to start again.")
            elif kind == "command":
                {"show": self.show, "start": self.start, "stop": self.stop, "quit": self.close}[value]()
                if self.closing:
                    return
        if self.session.latest is not None:
            self.draw(self.session.latest)
        if not self.closing:
            self.root.after(50, self.tick)

    def close(self):
        if not self.closing:
            self.closing = True
            self.save_settings()
            self.stop()
        if self.session.running:
            self.root.after(100, self.close)
            return
        if self.tray:
            self.tray.stop()
        self.root.destroy()

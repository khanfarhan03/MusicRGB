"""Validated per-user settings, stored outside the executable bundle."""
import json
import os
from pathlib import Path

from effects import MODES, PALETTES, parse_color

DEFAULTS = dict(mode="Song vibe", gain=1.0, brightness=0.8, smoothing=0.35,
    speed=1.0, noise_floor=0.0005, idle=0.0, palette="Neon", custom="#9b5cff",
    preview=False, topmost=False, stop_color="Light blue", device="",
    audio_source="Playback output")
PRESETS = {
    "Song vibe": dict(mode="Song vibe", gain=1, brightness=.75, smoothing=.65, speed=1, idle=.02),
    "Music wave": dict(mode="Music wave", gain=1.2, brightness=.85, smoothing=.25, speed=1.2, idle=0),
    "Balanced": dict(mode="Spectrum", gain=1, brightness=.8, smoothing=.35, speed=1, idle=0),
    "Bass night": dict(mode="Bass pulse", palette="Neon", gain=1.5, brightness=.7, smoothing=.2, speed=1, idle=0),
    "Immersive": dict(mode="Beat bloom", palette="Candy", gain=1.3, brightness=.9, smoothing=.22, speed=1.2, idle=.03),
    "Chill": dict(mode="Aurora", palette="Ice", gain=.8, brightness=.5, smoothing=.9, speed=.5, idle=.08),
    "Warm glow": dict(mode="Ember", gain=1, brightness=.65, smoothing=.7, speed=.7, idle=.06),
}


def validate(data):
    result = DEFAULTS.copy()
    if not isinstance(data, dict):
        return result
    for key, choices in (("mode", MODES), ("palette", PALETTES),
                         ("audio_source", ("Playback output", "Microphone input")),
                         ("stop_color", ("Light blue", "White", "Dim purple", "Off", "Keep last", "Custom colour"))):
        if isinstance(data.get(key), str) and data[key] in choices:
            result[key] = data[key]
    for key, low, high in (("gain", .2, 4), ("brightness", 0, 1), ("smoothing", 0, 1),
                          ("speed", .2, 3), ("noise_floor", 0, .02), ("idle", 0, .3)):
        value = data.get(key)
        if isinstance(value, (int, float)) and low <= value <= high:
            result[key] = float(value)
    for key in ("preview", "topmost"):
        if isinstance(data.get(key), bool):
            result[key] = data[key]
    if isinstance(data.get("device"), str):
        result["device"] = data["device"]
    try:
        parse_color(data.get("custom"))
        result["custom"] = data["custom"]
    except (ValueError, TypeError):
        pass
    return result


def settings_path():
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "MusicRGB" / "settings.json"


def load(path=None):
    try:
        return validate(json.loads((path or settings_path()).read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        return DEFAULTS.copy()


def save(data, path=None):
    path = path or settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(validate(data), indent=2), encoding="utf-8")
    temp.replace(path)

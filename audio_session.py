"""Bounded audio queue and one lighting writer, independent of the UI."""
import queue
import threading
import time

import numpy as np
import pyaudiowpatch as pa

from asus_keyboard import AsusKeyboard
from effects import ReactiveColor, parse_color


def get_devices(source="Playback output"):
    with pa.PyAudio() as audio:
        if source == "Microphone input":
            devices = [audio.get_device_info_by_index(i) for i in range(audio.get_device_count())]
            devices = [d for d in devices if int(d.get("maxInputChannels", 0)) > 0
                       and "loopback" not in d["name"].lower()]
        else:
            devices = list(audio.get_loopback_device_info_generator())
            try:
                default = audio.get_default_wasapi_loopback()["index"]
                devices.sort(key=lambda d: d["index"] != default)
            except OSError:
                pass
        return {f'{d["name"]} [{d["index"]}]': d for d in devices}


class AudioSession:
    def __init__(self, events):
        self.events = events
        self.stop_event = threading.Event()
        self.options = {}
        self.latest = None
        self.worker = None

    @property
    def running(self):
        return self.worker is not None and self.worker.is_alive()

    def start(self, device, options):
        if self.running:
            return
        self.options = options.copy()
        self.stop_event.clear()
        self.latest = None
        self.worker = threading.Thread(target=self.run, args=(device,), daemon=True)
        self.worker.start()

    def stop(self):
        self.stop_event.set()

    @staticmethod
    def finish_color(keyboard, options):
        choice = options.get("stop_color", "Light blue")
        if choice == "Keep last":
            return
        rgb = {"Light blue": (130, 200, 255), "White": (220, 220, 220),
               "Off": (0, 0, 0), "Dim purple": (40, 0, 70)}.get(choice, (130, 200, 255))
        if choice == "Custom colour":
            rgb = tuple(round(c*255*options["brightness"]) for c in parse_color(options["custom"]))
        keyboard.set_color(rgb)

    def run(self, device):
        keyboard = None
        packets = queue.Queue(maxsize=1)
        try:
            with pa.PyAudio() as audio:
                channels = int(device["maxInputChannels"])
                rate = int(device["defaultSampleRate"])
                def callback(data, count, timing, status):
                    try:
                        packets.put_nowait(data)
                    except queue.Full:
                        try:
                            packets.get_nowait()
                        except queue.Empty:
                            pass
                        try:
                            packets.put_nowait(data)
                        except queue.Full:
                            pass
                    return (None, pa.paContinue)
                stream = audio.open(format=pa.paFloat32, channels=channels, rate=rate,
                    input=True, input_device_index=int(device["index"]),
                    frames_per_buffer=max(512, rate//20), stream_callback=callback)
                engine = ReactiveColor()
                source = self.options.get("audio_source", "Playback output").lower()
                self.events.put(("status", f"Listening to {source}: " + device["name"].replace(" [Loopback]", "")))
                try:
                    while not self.stop_event.is_set():
                        started = time.monotonic()
                        options = self.options.copy()
                        try:
                            data = packets.get(timeout=.08)
                            samples = np.frombuffer(data, dtype=np.float32).reshape(-1, channels)
                        except queue.Empty:
                            samples = np.zeros((max(512, rate//20), channels), dtype=np.float32)
                        effect = {k: options[k] for k in ("mode", "gain", "brightness", "smoothing",
                            "speed", "noise_floor", "idle", "palette", "custom")}
                        rgb, level = engine.process(samples, rate, **effect)
                        if not options["preview"]:
                            if keyboard is None:
                                keyboard = AsusKeyboard()
                            keyboard.set_color(rgb)
                        elif keyboard is not None:
                            self.finish_color(keyboard, options)
                            keyboard.close()
                            keyboard = None
                        self.latest = dict(rgb=rgb, level=level, bars=engine.bars.copy(),
                            bands=engine.bands.copy(), beat=engine.beat, vibe=engine.vibe_label,
                            wave_levels=engine.wave_levels.copy(), wave_rgb=engine.wave_rgb.copy())
                        self.stop_event.wait(max(0, .05-(time.monotonic()-started)))
                        if not stream.is_active() and not self.stop_event.is_set():
                            raise RuntimeError("Audio output disconnected. Refresh outputs and start again.")
                finally:
                    stream.stop_stream()
                    stream.close()
        except Exception as exc:
            self.events.put(("error", str(exc)))
        finally:
            if keyboard is not None:
                try:
                    self.finish_color(keyboard, self.options)
                except Exception as exc:
                    self.events.put(("error", "Could not set the stop colour: " + str(exc)))
                keyboard.close()
            self.events.put(("done", None))

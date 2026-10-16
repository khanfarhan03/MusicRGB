"""Audio analysis, lighting effects, and a moving keyboard wave preview."""
import colorsys
import math
import time

import numpy as np

MODES = ("Song vibe", "Spectrum", "Music wave", "Bass pulse", "Beat bloom", "Rainbow", "Aurora", "Ember", "Ocean", "Custom colour")
PALETTES = {
    "Neon": ("#ff246d", "#7c4dff", "#20d9ed"),
    "Sunset": ("#ff3515", "#ffad33", "#b62393"),
    "Ice": ("#2355ff", "#16d9f0", "#d0f8ff"),
    "Forest": ("#127849", "#58db48", "#d3f96a"),
    "Candy": ("#f243ab", "#a761ff", "#54d9ee"),
}


def parse_color(value):
    if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
        raise ValueError("Expected a colour such as #7c4dff")
    return np.array([int(value[i:i+2], 16) / 255 for i in (1, 3, 5)])


class ReactiveColor:
    def __init__(self):
        self.level = 0.0
        self.bass = 0.0
        self.peak = 0.03
        self.beat = 0.0
        self.beat_average = 0.0
        self.beat_armed = True
        self.last_beat = -1e9
        self.beat_count = 0
        self.last_time = None
        self.phase = 0.0
        self.wave_phase = 0.5
        self.wave_levels = np.zeros(14)
        self.wave_rgb = np.zeros((14, 3), dtype=np.uint8)
        self.rgb = np.zeros(3)
        self.bars = np.zeros(18)
        self.bands = np.zeros(3)
        self.vibe_energy = 0.0
        self.vibe_balance = np.array([.33, .34, .33])
        self.vibe_color = parse_color("#8e70cf")
        self.vibe_label = "Listening for the song's character"

    def process(self, samples, rate, mode="Spectrum", gain=1.0, brightness=0.8,
                smoothing=0.35, speed=1.0, noise_floor=0.0005, idle=0.0,
                palette="Neon", custom="#9b5cff", now=None):
        now = time.monotonic() if now is None else now
        dt = 0.05 if self.last_time is None else max(0.001, min(0.25, now-self.last_time))
        self.last_time = now
        self.phase = (self.phase + dt * speed / 12) % 1
        self.wave_phase = (self.wave_phase + dt * speed / 5) % 1
        samples = np.asarray(samples, dtype=np.float32)
        if samples.ndim == 1:
            samples = samples[:, None]
        samples = np.clip(np.nan_to_num(samples, nan=0, posinf=0, neginf=0), -1, 1)
        rms = float(np.sqrt(np.mean(samples**2))) if samples.size else 0.0
        power = None
        bands = np.zeros(3)
        if len(samples) > 1:
            power = np.mean(np.abs(np.fft.rfft(samples * np.hanning(len(samples))[:, None], axis=0))**2, axis=1)
            freqs = np.fft.rfftfreq(len(samples), 1/rate)
            for i, (lo, hi) in enumerate(((35, 250), (250, 2500), (2500, 12000))):
                bands[i] = np.sqrt(power[(freqs >= lo) & (freqs < hi)].sum())
            edges = np.geomspace(35, min(rate/2, 16000), 19)
            raw = np.array([np.sqrt(power[(freqs >= lo) & (freqs < hi)].sum())
                            for lo, hi in zip(edges[:-1], edges[1:])])
            raw = np.log1p(raw)
            raw /= max(float(raw.max()), 1.0)
            self.bars = np.maximum(raw, self.bars * math.exp(-dt/0.18))
        self.bands = bands / max(float(bands.sum()), 1e-9)
        self.peak = max(rms, self.peak * math.exp(-dt/6), 0.015)
        target = min(1.0, max(0.0, rms-noise_floor) / self.peak * gain)
        tau = 0.025 + smoothing*0.10 if target > self.level else 0.06 + smoothing*0.5
        self.level += (1-math.exp(-dt/tau)) * (target-self.level)
        # Detect each bass swell against a slow local baseline. This catches
        # gradual wave-like beats without requiring a sharp frame-to-frame jump.
        # Rearm only after the swell falls back toward its local baseline, so a
        # long crest produces one pulse instead of repeated pulses.
        beat_energy = float(bands[0] + 0.35*bands[1])
        sensitivity = min(4.0, max(0.2, gain))
        beat_floor = max(1e-7, noise_floor*len(samples)*0.0015/math.sqrt(sensitivity))
        beat_gate = max(1e-5, noise_floor*0.25/math.sqrt(sensitivity))
        baseline_ratio = max(1.008, 1.035-0.007*sensitivity)
        if rms <= beat_gate or beat_energy < max(beat_floor, self.beat_average*0.995):
            self.beat_armed = True
        onset = (rms > beat_gate and self.beat_armed
                 and beat_energy > max(beat_floor, self.beat_average*baseline_ratio))
        if onset and now-self.last_beat > 0.19:
            self.beat = 1.0
            self.last_beat = now
            self.beat_count += 1
            self.beat_armed = False
        self.beat_average += (1-math.exp(-dt/2.0))*(beat_energy-self.beat_average)
        self.beat *= math.exp(-dt/(0.12+smoothing*0.35))
        self.bass += (1-math.exp(-dt/0.1))*(self.bands[0]-self.bass)
        colors = [parse_color(c) for c in PALETTES.get(palette, PALETTES["Neon"])]
        def blend(position):
            position = position % 1 * len(colors)
            i = int(position)
            return colors[i]*(1-(position-i)) + colors[(i+1)%len(colors)]*(position-i)
        # Build a traveling broad crest. Audio level controls the overall
        # height; the live spectrum adds local variation across the keys.
        positions = np.linspace(0, 1, len(self.wave_levels))
        distance = np.abs(positions-self.wave_phase)
        distance = np.minimum(distance, 1-distance)
        crest = np.exp(-0.5*(distance/0.22)**2)
        spectrum = np.interp(np.linspace(0, len(self.bars)-1, len(self.wave_levels)),
                             np.arange(len(self.bars)), self.bars)
        wave_target = np.clip(np.maximum(idle, self.level*(0.08+0.92*crest)*
                              (0.65+0.35*spectrum))*brightness, 0, 1)
        wave_tau = np.where(wave_target > self.wave_levels,
                            0.025+smoothing*0.10, 0.05+smoothing*0.25)
        self.wave_levels += (1-np.exp(-dt/wave_tau))*(wave_target-self.wave_levels)
        value = self.level
        if mode == "Song vibe":
            # Slow adaptation keeps one musical passage visually coherent.
            adapt = 1-math.exp(-dt/4)
            self.vibe_energy += adapt*(min(1, rms*5*gain)-self.vibe_energy)
            if rms > noise_floor:
                self.vibe_balance += adapt*(self.bands-self.vibe_balance)
            bass, mid, treble = self.vibe_balance
            if self.vibe_energy < .12:
                mood = "Soft / atmospheric"
                shade = (.24, .30, .72)
            elif bass > .55:
                mood = "Deep / bass driven"
                shade = (.65, .07, .40)
            elif treble > .30 and self.vibe_energy > .28:
                mood = "Bright / energetic"
                shade = (.05, .8, .72)
            elif mid > .38:
                mood = "Warm / mid focused"
                shade = (1, .35, .08)
            else:
                mood = "Open / balanced"
                shade = (.4, .15, .9)
            self.vibe_label = mood
            self.vibe_color += (1-math.exp(-dt/2.5))*(np.array(shade)-self.vibe_color)
            base = self.vibe_color
            value = max(self.level*(.35+.35*self.beat), .50*self.beat)
        elif mode == "Spectrum":
            hue = float(np.dot(self.bands, [0, 0.34, 0.66]))
            base = np.array(colorsys.hsv_to_rgb(hue, .92, 1))
        elif mode == "Music wave":
            base = blend(self.wave_phase)
            base /= max(float(base.max()), 1e-9)
            value = self.level
        elif mode == "Bass pulse":
            base = blend(0.05+self.bass*0.45)
            value *= .25+.75*self.bass
        elif mode == "Beat bloom":
            base = blend(self.beat_count*.19)
            # Keep detected hits visible even when the whole track is quiet.
            value = max(self.level*.14, .65*self.beat)
        elif mode == "Rainbow":
            base = np.array(colorsys.hsv_to_rgb(self.phase, .92, 1))
        elif mode == "Aurora":
            base = blend(self.phase+.12*self.bass)
        elif mode == "Ember":
            base = np.array((1, .05+.50*self.level, .01+.07*self.beat))
        elif mode == "Ocean":
            base = np.array((.03+.15*self.beat, .20+.65*self.bass, 1))
        else:
            base = parse_color(custom)
        value = max(idle, value)*brightness
        target_rgb = np.clip(base*value, 0, 1)
        color_tau = .008+smoothing*.12
        self.rgb += (1-math.exp(-dt/color_tau))*(target_rgb-self.rgb)
        for i, intensity in enumerate(self.wave_levels):
            wave_color = blend(self.wave_phase+i/len(self.wave_levels))
            self.wave_rgb[i] = np.rint(np.clip(wave_color*intensity*255, 0, 255)).astype(np.uint8)
        return tuple(int(round(c*255)) for c in self.rgb), self.level

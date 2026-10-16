import unittest
import numpy as np
from music_rgb import ReactiveColor
from effects import MODES


class AudioTests(unittest.TestCase):
    rate = 48000

    def tone(self, frequency, amplitude=0.1):
        t = np.arange(2400) / self.rate
        channel = amplitude * np.sin(2 * np.pi * frequency * t)
        return np.column_stack((channel, -channel))

    def test_silence_is_dark(self):
        for mode in ("Spectrum", "Bass pulse", "Rainbow"):
            rgb, level = ReactiveColor().process(np.zeros((2400, 2)), self.rate, mode)
            self.assertEqual(rgb, (0, 0, 0))
            self.assertEqual(level, 0)

    def test_spectrum_tracks_frequency_without_stereo_cancellation(self):
        for frequency, expected_channel in ((80, 0), (1000, 1), (6000, 2)):
            rgb, level = ReactiveColor().process(self.tone(frequency), self.rate)
            self.assertEqual(int(np.argmax(rgb)), expected_channel)
            self.assertGreater(level, 0)

    def test_brightness_scales_output(self):
        tone = self.tone(80)
        bright, _ = ReactiveColor().process(tone, self.rate, brightness=1)
        dim, _ = ReactiveColor().process(tone, self.rate, brightness=0.2)
        self.assertLess(max(dim), max(bright))

    def test_release_fades_to_black(self):
        engine = ReactiveColor()
        engine.process(self.tone(80), self.rate, now=0)
        for i in range(1, 81):
            rgb, _ = engine.process(np.zeros((2400, 2)), self.rate, now=i*.05)
        self.assertEqual(rgb, (0, 0, 0))

    def test_all_effects_stay_in_range(self):
        for mode in MODES:
            engine = ReactiveColor()
            for i in range(40):
                rgb, _ = engine.process(self.tone(80+i*200), self.rate, mode,
                                        gain=4, brightness=1, now=i*.05)
                self.assertTrue(all(0 <= value <= 255 for value in rgb))

    def test_song_vibe_is_repeatable_and_not_a_clock_cycle(self):
        a, b = ReactiveColor(), ReactiveColor()
        for i in range(160):
            # Different wall-clock offsets must not change this audio-driven effect.
            ra, _ = a.process(self.tone(80), self.rate, "Song vibe", now=i*.05)
            rb, _ = b.process(self.tone(80), self.rate, "Song vibe", now=1000+i*.05)
            self.assertEqual(ra, rb)
        self.assertIn("bass", a.vibe_label)

    def test_song_vibe_palette_changes_with_audio_character(self):
        a, b = ReactiveColor(), ReactiveColor()
        for i in range(200):
            ra, _ = a.process(self.tone(80, .2), self.rate, "Song vibe", now=i*.05)
            rb, _ = b.process(self.tone(1000, .2), self.rate, "Song vibe", now=i*.05)
        self.assertNotEqual(a.vibe_label, b.vibe_label)
        self.assertNotEqual(ra, rb)


if __name__ == "__main__":
    unittest.main()

import tempfile
from pathlib import Path
import unittest

import settings
from audio_session import AudioSession


class SettingsTests(unittest.TestCase):
    def test_invalid_values_cannot_break_effects(self):
        bad = dict(mode="fake", brightness=float("nan"), gain=900,
                   custom="#zzzzzz", palette="unknown", preview="yes")
        self.assertEqual(settings.validate(bad), settings.DEFAULTS)

    def test_saved_preset_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"preset.json"
            values = settings.DEFAULTS | settings.PRESETS["Chill"]
            settings.save(values, path)
            self.assertEqual(settings.load(path), values)

    def test_malformed_settings_fall_back(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"settings.json"
            path.write_text("bad json")
            self.assertEqual(settings.load(path), settings.DEFAULTS)

    def test_nested_invalid_values_fall_back(self):
        self.assertEqual(settings.validate(dict(mode=[], palette={}, custom=[])), settings.DEFAULTS)

    def test_stop_colours(self):
        class Keyboard:
            colour = None
            def set_color(self, rgb):
                self.colour = rgb
        keyboard = Keyboard()
        AudioSession.finish_color(keyboard, settings.DEFAULTS)
        self.assertEqual(keyboard.colour, (130, 200, 255))
        white = settings.validate(settings.DEFAULTS | dict(stop_color="White"))
        AudioSession.finish_color(keyboard, white)
        self.assertEqual(keyboard.colour, (220, 220, 220))
        AudioSession.finish_color(keyboard, settings.DEFAULTS | dict(stop_color="Keep last"))
        self.assertEqual(keyboard.colour, (220, 220, 220))


if __name__ == "__main__":
    unittest.main()

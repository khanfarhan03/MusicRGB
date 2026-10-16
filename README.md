# Music RGB Immersive

Music RGB is a Windows audio-reactive lighting app with a conservative,
model-specific keyboard layer. It is **not universally compatible**: internal
laptop keyboards do not share a Windows lighting API. Unsupported machines can
use audio preview without the app attempting keyboard writes. See
[COMPATIBILITY.md](COMPATIBILITY.md) for researched adapters, evidence levels,
limitations and the support roadmap.

This project is licensed under the [MIT License](LICENSE).

## Open the app

Run `Setup.cmd` once, then open `Launch.cmd`. Setup creates a fresh
`.venv-vivobook` environment so it does not reuse the stale Python 3.11
environment in the project folder. Launch runs the laptop-specific source app.
`Build.cmd` creates `dist\MusicRGB-MusicWave.exe` after setup; use `Launch.cmd`
to run the source app.

Select the audio output playing music, choose **Music wave** and click **Start
sync**. Set keyboard brightness above zero using the laptop controls. With
SteelSeries Sonar, select the channel carrying music or the physical speakers
receiving it. Use Refresh outputs after changing devices while stopped.

The current direct hardware adapters are limited to identified ASUS model
families. The Vivobook 16 X1605VA uses a white one-zone backlight with three
lit firmware levels plus off; its per-key wave is preview-only. Selected TUF
FA/FX families use an ASUS ATKACPI RGB protocol; the app checks controller
support read-only before sending any color command. Exact models are not all
hardware-tested. TUF output is currently a uniform keyboard color, not a
per-key spatial wave. Listed ROG and Vivobook families are identified as
vendor-software candidates but remain preview-only in Music RGB until their
specific integration is added. Other brands and ASUS models also run in
preview mode.

## Effects

- **Song vibe:** gradually chooses a palette from measured loudness and bass,
  midrange and treble balance. Softer passages use muted blue/violet; bass-heavy
  passages use magenta; prominent mids use amber; energetic treble uses teal.
  The estimate adapts over several seconds, with subtle bass-onset pulses.
  This is an audio heuristic, not emotion or genre recognition. Playback volume
  affects it. It does not read lyrics, album art or Spotify metadata.
- **Spectrum:** colours follow the frequency balance.
- **Music wave:** a bright crest travels across the keyboard preview while its
  height follows live audio energy and its shape responds to the spectrum. Low
  volume stays dim; louder passages rise brighter. On the Vivobook, the actual
  keyboard follows the overall audio level uniformly because its backlight has
  no independently controlled key zones.
- **Bass pulse:** emphasises low frequencies with your selected palette.
- **Beat bloom:** changes palette colour on estimated bass onsets, including
  slow, wave-like bass swells. It gives one pulse as each swell rises instead
  of waiting for a sharp hit. It does not calculate an exact BPM or beat grid.
  Song vibe also pulses with detected onsets.
- **Rainbow:** cycles hue with intensity driven by audio.
- **Aurora:** drifts through a palette with bass accents.
- **Ember:** red and amber that respond to music energy.
- **Ocean:** blue and teal with bass accents.
- **Custom colour:** audio controls the brightness of your chosen hue.

Palettes apply to Bass pulse, Beat bloom and Aurora. Song vibe chooses its own
colours from the audio. On this Vivobook, these color choices influence the
preview; the physical keyboard remains white and follows the calculated
brightness. Sensitivity also sets how easily quiet bass onsets register; raise
it if gentle beats are missed, and lower it if steady music causes extra
pulses. Adjust smoothness, sensitivity, brightness, speed, silence
threshold and optional glow during silence. Set glow to zero to fade to
darkness when playback stops. The control panel includes a live spectrum.

## Presets and settings

Built-in presets include Music wave, Song vibe, Balanced, Bass night, Immersive,
Chill and Warm glow. Save preset exports a named JSON file; Load imports one. Keep as
many files as you want. Save settings remembers the current controls; quitting
also saves to `%LOCALAPPDATA%\MusicRGB\settings.json`.

Stop leaves the backlight at a medium level by default. You can choose White,
Light blue, Dim purple, Off, Keep last or Custom colour under When sync stops;
the non-white colors map to white backlight intensity levels on this model.
The current ASUS adapter does not capture and restore a complete prior lighting
profile; its stop behavior uses the selected stop color. Keep this limitation in
mind before using it alongside OEM lighting software.
Switching to Preview only during hardware
sync applies the stop colour once, then releases the controller. Subsequent
frames are only shown in the preview.

## Tray controls

Hide to tray keeps sync running without the main window. Right-click the icon
beside the Windows clock to show controls, start/resume, stop or quit.
Closing the main window quits completely; it does not leave capture running.
No startup task is installed. Keep window on top is optional.

## Troubleshooting and privacy

The locally built `dist\MusicRGB-MusicWave.exe` is unsigned, so Windows Smart
App Control may block it. This project has a ready-to-use Python environment;
try `Launch.cmd` to start the same app from source. If Windows blocks that
launcher too, this build needs to be signed with a trusted code-signing
certificate. Smart App Control does not offer an allow-one-app exception.

If driver access is denied, run Launch.cmd as administrator. If another app
overwrites colours, disable its active lighting effect. This app does not stop
ASUS services, install drivers, change power profiles or control fans.

Choose **Playback output** to capture the selected Windows loopback, or
**Microphone input** to capture the selected recording device. Selecting the
microphone explicitly authorizes capture while sync is active; Windows privacy
settings may still block it. Audio is processed locally in memory. Spotify,
browsers and local players need no account integration. Protected playback or
exclusive audio drivers may not provide usable loopback audio. A disconnected
device requires selecting it again and restarting sync.

Audio is processed in memory, never saved or uploaded. Error logs, containing
no audio, are written to `%LOCALAPPDATA%\MusicRGB\music_rgb.log`.

## Development and tests

Setup.cmd creates a source environment. Build.cmd installs build dependencies,
runs tests and packages a single executable with PyInstaller.

```
.venv-vivobook\Scripts\python.exe -m unittest -v test_audio test_settings
.venv-vivobook\Scripts\python.exe music_rgb.py --diagnose --report diagnostics.json
.venv-vivobook\Scripts\python.exe music_rgb.py --smoke-test-report source-smoke-test.json
dist\MusicRGB-MusicWave.exe --smoke-test-report packaged-smoke-test.json
```

Smoke tests initialise the GUI and tray, capture playback in preview mode,
stop and write a JSON report. They do not save settings or change lights.
The X1605VA uses the ASUS keyboard-brightness ACPI endpoint (`0x00050021`).
Selected TUF FA/FX families use the ASUS RGB endpoints after a read-only
support check. Diagnostics identify the system model and avoid probing ASUS
endpoints on non-ASUS systems. They do not verify lighting by changing it.

See [COMPATIBILITY.md](COMPATIBILITY.md) for the compatibility policy,
integration research and roadmap. No other manufacturer is currently enabled
for direct hardware writes.

Technical references:

- https://github.com/seerge/g-helper/blob/main/app/AsusACPI.cs
- https://github.com/s0d3s/PyAudioWPatch
- https://pystray.readthedocs.io/en/latest/usage.html
- https://pyinstaller.org/en/stable/usage.html

# Keyboard compatibility and support policy

Music RGB is not a universal laptop-keyboard controller. Laptop vendors use
different firmware, ACPI/WMI methods, USB controllers and per-key layouts.
Windows has no built-in API that can set the color or brightness of every
internal keyboard. SMBIOS identification tells us the machine model, not that a
particular light controller is installed or writable.

## Status definitions

- **Verified:** tested by this project on the exact machine/SKU and lighting
  controller, with repeatable audio capture, frame writes, stop and cleanup.
- **Protocol known:** a model-family-specific interface is implemented, but the
  exact unit has not passed this project's hardware test process. Do not treat
  this as verified support.
- **Candidate:** an official SDK or maintained open-source implementation may
  provide a route. No controller is enabled by Music RGB yet.
- **Unsupported:** no safe adapter is available. Preview mode still works.

## Current project inventory

| Device / family | Detected lighting | Adapter | Current status and limits |
|---|---|---|---|
| ASUS Vivobook 16 X1605VA | White, one zone, four firmware states including off | ASUS ATKACPI keyboard-brightness endpoint | Protocol known; physical unit was used during earlier project development. No per-key spatial wave or color commands. |
| ASUS TUF FA506/FA507/FA608/FA706 and selected FX506/FX507/FX607 families | RGB configurations vary; this adapter writes one uniform color | ASUS ATKACPI RGB endpoints, with a read-only support probe before writes | Protocol-known from G-Helper's ASUS ACPI implementation; exact units are not tested here. Unsupported endpoint => no command sent. Uniform output only; no spatial wave. |
| ASUS ROG Strix G614/G615/G814/G815 | RGB layout varies by SKU | Armoury Crate / Aura Creator candidate | Detected and identified in the app, but no Music RGB hardware adapter. Use Aura Creator's Music effect only if the exact keyboard appears as compatible. |
| ASUS ROG Zephyrus GU405/GU605/GA605 | RGB layout varies by exact SKU | Armoury Crate / Aura Creator candidate | Detected and identified in the app, but no Music RGB hardware adapter. |
| ASUS Vivobook S5606/S5406/S5507/K5504 and S530 | RGB or backlit-only depending on exact SKU | No Music RGB adapter | The app reports a candidate family only; verify the exact SKU and do not assume RGB. |
| Other ASUS models | Unknown | None selected | Unsupported; never infer controller support from ASUS branding. |
| Acer, HP, Dell/Alienware, Lenovo, MSI, Gigabyte, Razer and others | Unknown until exact SKU/controller is identified | None selected | Unsupported by direct Music RGB hardware writes. Audio preview is available. |

This table intentionally does not turn OpenRGB's general device list into a
claim about laptop support. OpenRGB has individual laptop keyboard controllers
and a network SDK, but support depends on the exact controller, release and
device entry. It can be considered as an optional adapter only after a real
device is reported and written safely.

## Integration candidates researched

- **OpenRGB SDK:** cross-vendor SDK/server for devices OpenRGB actually
  supports. Potential adapter for enumerated laptop keyboards; server presence
  alone is not evidence that an internal keyboard is supported. The SDK is
  network-based, so Music RGB should connect only to an explicitly selected
  local server by default.
- **ASUS Aura SDK / Aura Creator:** official APIs and a documented music-sync
  effect exist for compatible Aura devices. Compatibility is not universal to
  ASUS laptops; some models use separate keyboard firmware interfaces.
- **Razer Chroma SDK:** official integration route for supported Chroma devices
  with the Razer service installed. Must confirm whether the particular laptop
  keyboard is exposed to that SDK.
- **HP OMEN Light Studio:** official software documents audio visualizer modes
  on compatible OMEN lighting zones. This is a vendor-app route, not a general
  hardware API for every HP laptop.
- **SteelSeries GG Audio Visualizer:** third-party audio-reactive feature for
  supported Prism devices. A SteelSeries keyboard vendor inside an MSI laptop
  is not by itself proof the integrated keyboard is exposed as a supported
  Prism device.
- **Acer PredatorSense, Lenovo Spectrum, Alienware Command Center, Gigabyte
  Control Center:** official lighting customization exists on selected models;
  this review did not establish a universal third-party audio waveform API for
  their laptop keyboards.

Research links:

- OpenRGB project and SDK: https://openrgb.org/
- OpenRGB supported-device list: https://openrgb.org/devices_pipeline.html
- ASUS Aura SDK: https://www.asus.com/microsite/aurareadydevportal/
- ASUS Aura Creator music effect: https://rog.asus.com/uk/support/faq/1042503/
- Razer Chroma developer portal: https://developer.razer.com/chroma./
- HP OMEN Light Studio audio visualizer: https://support.hp.com/ie-en/document/ish_9282184-5659745-16
- SteelSeries Audio Visualizer: https://support.steelseries.com/hc/en-us/articles/48540958895501-How-to-Enable-Audio-Visualizer
- ASUS ACPI protocol reference used by the existing adapter:
  https://github.com/seerge/g-helper/blob/main/app/AsusACPI.cs

## Adapter requirements

Each future adapter must implement `KeyboardBackend` in `keyboard_backends.py`
and report identity, lighting type, addressable zones/keys, color capability,
control granularity, and status. It must:

1. Match a specific hardware/controller identity, not just a manufacturer.
2. Probe read-only first and refuse writes when the controller is ambiguous.
3. Capture the previous state where the protocol permits it, and restore it on
   normal stop, application exit and recoverable errors. If it cannot capture
   and restore, disclose that before enabling hardware output.
4. Keep one writer thread per device and bound/replace stale audio frames.
5. Avoid stopping, disabling or fighting OEM services. Detect likely conflicts
   and explain them to the user.
6. Be verified on physical hardware for every advertised configuration. Record
   model/SKU, controller IDs, OS/build, OEM software version, adapter version,
   tests performed and limitations in `compatibility-results/`.

## Roadmap

1. **Discovery and safe unsupported path (current):** report SMBIOS vendor/model
   and the exact known adapter status; preview works without keyboard writes.
2. **Read-only OpenRGB discovery:** optional local SDK connection, enumerate
   devices and show the exact detected controller and zones without changing
   them.
3. **Controlled RGB adapter:** add OpenRGB writes behind explicit device
   selection, state backup when available, a preview-to-hardware confirmation,
   and a stop/restore path; validate on physical laptop keyboards.
4. **Vendor adapters:** pursue official SDKs where they expose the built-in
   keyboard and lifecycle/state APIs. Add models independently as evidence is
   collected.
5. **Microphone input:** add explicit input-device selection and permission
   disclosure. Current capture is Windows playback loopback only.
6. **Release matrix:** publish a model/SKU support table with verified status,
   diagnostic bundle format, install instructions and known conflicts.

## Diagnostics and privacy

Run `.venv-vivobook\\Scripts\\python.exe music_rgb.py --diagnose --report diagnostics.json`
for a diagnostic report. Diagnostics report system identity and perform
read-only ASUS endpoint probes only on the identified ASUS families. They do
not record audio. The app can capture a selected Windows playback loopback or,
when explicitly selected, microphone input; audio is processed in memory.

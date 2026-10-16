"""Capability discovery and backend contracts for built-in laptop keyboards.

Detection is deliberately separate from support: an OEM/model match is not
proof that a controller is present or writable. Only adapters with a known,
model-specific protocol may advertise control.
"""
from dataclasses import asdict, dataclass
import os
import platform


@dataclass(frozen=True)
class KeyboardInfo:
    manufacturer: str
    model: str
    lighting: str
    zones: int | None
    color: bool | None
    status: str
    backend: str | None = None
    note: str = ""

    def to_dict(self):
        return asdict(self)


def system_identity():
    """Read Windows SMBIOS identity without installing a dependency."""
    manufacturer, model = platform.system(), platform.machine()
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                    r"HARDWARE\DESCRIPTION\System\BIOS") as key:
                def read(name, fallback):
                    try:
                        return str(winreg.QueryValueEx(key, name)[0]).strip()
                    except OSError:
                        return fallback
                manufacturer = read("SystemManufacturer", manufacturer)
                model = read("SystemProductName", model)
        except OSError:
            pass
    return manufacturer, model


_DETECTORS = []


def register_detector(detector):
    """Register a detector callable accepting (manufacturer, model)."""
    _DETECTORS.append(detector)


def _detect_asus(manufacturer, model):
    if "asus" not in manufacturer.lower():
        return None
    from asus_keyboard import laptop_profile
    _, profile = laptop_profile()
    if profile == "vivobook-white":
        return KeyboardInfo(manufacturer, model, "white single-zone", 1, False,
            "protocol-known; hardware previously observed on this exact family",
            "asus-atkacpi", "Four firmware brightness states (off plus three levels); no spatial wave.")
    if profile == "tuf-rgb":
        return KeyboardInfo(manufacturer, model, "RGB", 1, True,
            "protocol-known; read-only controller probe required; exact unit unverified",
            "asus-atkacpi",
            "TUF FA506/FA507/FA608/FA706 and selected FX506/FX507/FX607 families. A supported endpoint is checked before any write. Output is uniform; no per-key wave.")
    upper = model.upper()
    catalog = (
        (("G614", "G615", "G814", "G815"), "ROG Strix RGB (zone count varies by SKU)",
         "Armoury Crate / Aura Creator candidate; keyboard control is not integrated."),
        (("GU405",), "ROG Zephyrus G14 1-zone RGB (listed configurations)",
         "Armoury Crate / Aura Creator candidate; keyboard control is not integrated."),
        (("GU605", "GA605"), "ROG Zephyrus G16 RGB (SKU-dependent)",
         "Armoury Crate / Aura Creator candidate; verify the exact SKU."),
        (("S5606", "S5406", "S5507", "K5504"), "Vivobook S RGB (listed configurations)",
         "No Music RGB adapter. Verify backlight and color support for the exact SKU."),
        (("S530",), "Vivobook S15 backlit (color type SKU-dependent)",
         "Backlight only; RGB capability is not assumed."),
    )
    for identifiers, lighting, note in catalog:
        if any(identifier in upper for identifier in identifiers):
            return KeyboardInfo(manufacturer, model, lighting, None, None,
                "vendor software candidate; direct control unsupported", None, note)
    return KeyboardInfo(manufacturer, model, "unknown", None, None, "unsupported",
        note="No model-specific safe lighting adapter is registered.")


register_detector(_detect_asus)


def discover_keyboard():
    """Return conservative capability status; never infer lighting from brand."""
    manufacturer, model = system_identity()
    for detector in _DETECTORS:
        result = detector(manufacturer, model)
        if result is not None:
            return result
    return KeyboardInfo(manufacturer, model, "unknown", None, None, "unsupported",
        note="Model detected, but no verified built-in keyboard adapter is registered. Audio preview remains available.")


def compatibility_report():
    """Discovery result for diagnostics and UI; this does not write to hardware."""
    return discover_keyboard().to_dict()


class KeyboardBackend:
    """Backend contract for future vendor/OpenRGB adapters."""
    info: KeyboardInfo

    def probe(self):
        raise NotImplementedError

    def apply_frame(self, rgb, columns=None):
        raise NotImplementedError

    def restore(self):
        raise NotImplementedError

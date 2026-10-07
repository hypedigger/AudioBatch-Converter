"""
Windows 11 visual effects via DWM (Desktop Window Manager).
Applies Acrylic backdrop and rounded corners to a QWidget window.
"""
import ctypes
import ctypes.wintypes
import sys


# ── DWM attribute constants ─────────────────────────────────────────────────

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33   # Win11 21H2+
DWMWA_SYSTEMBACKDROP_TYPE      = 38   # Win11 22H2+

DWMWCP_ROUND    = 2
DWMSBT_ACRYLIC  = 3   # Acrylic (22H2+)
DWMSBT_MICA     = 2   # Mica (fallback)

# Older accent-policy approach (pre-22H2)
WCA_ACCENT_POLICY              = 19
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4


class _ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState",   ctypes.c_int),
        ("AccentFlags",   ctypes.c_int),
        ("GradientColor", ctypes.c_int),
        ("AnimationId",   ctypes.c_int),
    ]


class _WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute",  ctypes.c_int),
        ("Data",       ctypes.POINTER(ctypes.c_int)),
        ("SizeOfData", ctypes.c_size_t),
    ]


def _dwm_set_attr(hwnd: int, attr: int, value: int) -> bool:
    try:
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, attr,
            ctypes.byref(ctypes.c_int(value)),
            ctypes.sizeof(ctypes.c_int),
        )
        return True
    except Exception:
        return False


def apply_acrylic(hwnd: int, dark: bool = True) -> None:
    """
    Apply Acrylic blur + optional dark-mode title bar to *hwnd*.
    Falls back gracefully on older Windows builds.
    """
    if sys.platform != "win32":
        return

    # Dark / light mode for the non-client area
    _dwm_set_attr(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 1 if dark else 0)

    # Rounded corners (Win11)
    _dwm_set_attr(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND)

    # Try Win11 22H2+ Acrylic backdrop first
    if _dwm_set_attr(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, DWMSBT_ACRYLIC):
        return

    # Fallback: accent-policy Acrylic (older Win11 / Win10)
    try:
        user32 = ctypes.windll.user32
        accent = _ACCENT_POLICY()
        accent.AccentState   = ACCENT_ENABLE_ACRYLICBLURBEHIND
        accent.AccentFlags   = 2
        accent.GradientColor = 0x0A0A0A18  # ABGR semi-transparent

        data = _WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute  = WCA_ACCENT_POLICY
        data.SizeOfData = ctypes.sizeof(accent)
        data.Data       = ctypes.cast(ctypes.byref(accent), ctypes.POINTER(ctypes.c_int))

        user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
    except Exception:
        pass


def apply_acrylic_light(hwnd: int) -> None:
    apply_acrylic(hwnd, dark=False)

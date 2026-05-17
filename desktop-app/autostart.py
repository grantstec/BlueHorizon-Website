"""Manage the Windows 'Run on startup' registry entry for this app.

Uses HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run, which does NOT
require admin rights. The value points at the running .exe with a
`--minimized` flag so the window opens into the taskbar instead of popping up
in the user's face every time Windows boots.

On non-Windows OSes (or when running from source rather than a frozen .exe),
all functions become safe no-ops / return False so the GUI can hide the
toggle gracefully.
"""

from __future__ import annotations

import os
import sys


APP_REG_NAME = "BlueHorizonDesktop"
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def is_supported() -> bool:
    """True when toggling autostart will actually do something useful.

    We require: Windows + a frozen PyInstaller executable. When running from
    `python main.py` we'd otherwise register a path to the Python interpreter,
    which is fragile and would silently break the moment the dev's venv moved.
    """
    if os.name != "nt":
        return False
    return getattr(sys, "frozen", False)


def _autostart_command() -> str:
    """Quoted command line written into the Run key."""
    exe = sys.executable
    return f'"{exe}" --minimized'


def is_enabled() -> bool:
    if os.name != "nt":
        return False
    try:
        import winreg  # type: ignore
    except ImportError:
        return False
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ
        ) as k:
            value, _ = winreg.QueryValueEx(k, APP_REG_NAME)
            return bool(value)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def enable() -> None:
    """Add (or refresh) the Run-on-startup entry."""
    if os.name != "nt":
        raise RuntimeError("Autostart is only supported on Windows.")
    import winreg  # type: ignore

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
    ) as k:
        winreg.SetValueEx(
            k, APP_REG_NAME, 0, winreg.REG_SZ, _autostart_command()
        )


def disable() -> None:
    """Remove the Run-on-startup entry if it exists."""
    if os.name != "nt":
        return
    try:
        import winreg  # type: ignore
    except ImportError:
        return
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
        ) as k:
            try:
                winreg.DeleteValue(k, APP_REG_NAME)
            except FileNotFoundError:
                pass
    except FileNotFoundError:
        pass  # Run key itself doesn't exist — nothing to do

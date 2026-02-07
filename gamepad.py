"""Utility module extracted from `quickdupeobfus.py`.

Provides thin wrappers to initialize and access a virtual Xbox 360 controller
via the `vgamepad` (ViGEm) library.

Functions:
- install_vigem(): launch bundled ViGEmBus installer if present
- init_gamepad(): try to import/create a virtual gamepad (returns True on success)
- get_gamepad(): return the created gamepad instance or None

This module intentionally keeps imports lazy so the main application can run
even when ViGEmBus / vgamepad isn't installed.
"""

from __future__ import annotations

import os
import sys
import subprocess
import logging
import threading
import time
from typing import Optional

log = logging.getLogger("QuickDupe.gamepad")

# vgamepad module reference (set when available)
vg = None

# The created virtual gamepad (vx360) instance
_gamepad = None

# Warn flag if ViGEm problems were detected
_vigem_warned = False


def install_vigem() -> bool:
    """Run the bundled ViGEmBus installer if available.

    Returns True if the installer was launched, False otherwise.
    """
    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    installer_path = os.path.join(base_path, "ViGEmBus_1.22.0_x64_x86_arm64.exe")

    if os.path.exists(installer_path):
        log.info("Launching ViGEmBus installer: %s", installer_path)
        try:
            subprocess.Popen([installer_path])
            return True
        except Exception:
            log.exception("Failed to launch ViGEmBus installer")
            return False
    else:
        log.warning("ViGEmBus installer not found at: %s", installer_path)
        return False


def init_gamepad() -> bool:
    """Attempt to import `vgamepad` and create a virtual Xbox controller.

    Returns True on success. On failure this will attempt to auto-run the
    bundled ViGEmBus installer and set a warn flag.
    """
    global _gamepad, vg, _vigem_warned

    try:
        import vgamepad as vgamepad_module
        vg = vgamepad_module
        _gamepad = vg.VX360Gamepad()
        # Reset any stray state and push an initial update
        try:
            _gamepad.reset()
        except Exception:
            # Older versions may not expose reset; ignore
            pass
        try:
            _gamepad.update()
        except Exception:
            # Some environments may raise until driver is fully available
            pass
        log.info("Virtual Xbox controller initialized")
        return True
    except Exception as exc:
        log.warning("ViGEmBus/vgamepad initialization failed: %s", exc)
        # Attempt to auto-install driver if present alongside the application
        if install_vigem():
            log.info("ViGEmBus installer launched. Please restart the application once installation completes.")
        else:
            log.warning("Please install ViGEmBus manually: https://github.com/nefarius/ViGEmBus/releases")
        _vigem_warned = True
        return False


def get_gamepad():
    """Return the current VX360Gamepad instance or None if not initialized."""
    return _gamepad


def vigem_warned() -> bool:
    """Return True if an initialization attempt failed and the user was warned."""
    return _vigem_warned


# def _show_vigembus_help(self):
#     """Show popup with clickable links for ViGEmBus help"""
#     import webbrowser

#     popup = tk.Toplevel(self.root)
#     popup.title("ViGEmBus Setup")
#     popup.configure(bg='#1e1e1e')
#     popup.geometry("450x380")
#     popup.resizable(False, False)
#     popup.transient(self.root)
#     popup.grab_set()

#     # Center on parent
#     popup.update_idletasks()
#     x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (225)
#     y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (140)
#     popup.geometry(f"+{x}+{y}")

#     tk.Label(popup, text="ViGEmBus is preferred for consistency.",
#                 bg='#1e1e1e', fg='#e0e0e0', font=('Segoe UI', 10, 'bold')).pack(pady=(15, 10))

#     tk.Label(popup, text="Step 1: Install ViGEmBus driver",
#                 bg='#1e1e1e', fg='#e0e0e0', font=('Segoe UI', 9)).pack(pady=(5, 2))
#     link1 = tk.Label(popup, text="https://github.com/nefarius/ViGEmBus/releases",
#                     bg='#1e1e1e', fg='#4da6ff', cursor='hand2', font=('Segoe UI', 9, 'underline'))
#     link1.pack()
#     link1.bind('<Button-1>', lambda e: webbrowser.open("https://github.com/nefarius/ViGEmBus/releases"))

#     tk.Label(popup, text="\nStep 2: If still not working, also install:",
#                 bg='#1e1e1e', fg='#e0e0e0', font=('Segoe UI', 9)).pack(pady=(5, 2))
#     link2 = tk.Label(popup, text="Xbox 360 Accessories Software",
#                     bg='#1e1e1e', fg='#4da6ff', cursor='hand2', font=('Segoe UI', 9, 'underline'))
#     link2.pack()
#     link2.bind('<Button-1>', lambda e: webbrowser.open("https://community.pcgamingwiki.com/files/file/2630-xbox-360-accessories-software-v12/"))

#     tk.Label(popup, text="\nStep 3: If STILL not working:",
#                 bg='#1e1e1e', fg='#e0e0e0', font=('Segoe UI', 9)).pack(pady=(5, 2))
#     tk.Label(popup, text="Check the drag & drop box and record\ndrag paths for every macro you use.",
#                 bg='#1e1e1e', fg='#aaaaaa', font=('Segoe UI', 9)).pack()

#     ttk.Button(popup, text="Close", command=popup.destroy).pack(pady=15)

__all__ = [
    "install_vigem",
    "init_gamepad",
    "get_gamepad",
    "vg",
    "vigem_warned",
]

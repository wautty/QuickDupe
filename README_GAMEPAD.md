Gamepad helper (gamepad.py)
=============================

This small module extracts the ViGEm / vgamepad related helpers from
`quickdupeobfus.py` so other modules can initialize and use a virtual Xbox
360 controller.

Files
- `gamepad.py` — exposes `init_gamepad()`, `get_gamepad()`, `install_vigem()` and
  `vg` (the imported vgamepad module when available).

Quick usage
-----------

1. Initialize the gamepad early in your application (e.g. at startup):

```python
from gamepad import init_gamepad, get_gamepad, vg

# Try to initialize. Returns True on success.
if init_gamepad():
    gp = get_gamepad()
    # Example: press A, release A
    gp.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    gp.update()
    gp.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    gp.update()
else:
    # ViGEm not available — either call install_vigem() or fall back to
    # mouse/keyboard drag-drop logic.
    print("ViGEm not available; falling back to alternate input methods")
```

Notes
-----
- This module performs lazy import of `vgamepad`. If the import fails the
  `init_gamepad()` function will attempt to run a bundled ViGEmBus installer
  (if present next to the application). It does not automatically restart the
  app — you must restart after installing the driver.
- `get_gamepad()` returns the VX360Gamepad instance created by `init_gamepad()`
  or `None` if initialization failed.
- This is Windows-specific; vgamepad / ViGEmBus are required to present a
  system virtual controller.

API Reference (short)
- install_vigem() -> bool : Launch bundled installer if present.
- init_gamepad() -> bool : Try to create virtual controller; returns True on success.
- get_gamepad() -> VX360Gamepad|None : Return the created controller instance.
- vg : The imported vgamepad module (None until initialized).

from __future__ import annotations

from typing import Callable, Dict, Tuple

import ctypes

from pynput.keyboard import Key
from pynput.mouse import Button as MouseButton

Position = Tuple[int, int]


def run_quick_dupe_items(
    *,
    vsleep: Callable[[int], None],
    curved_drag: Callable[[Position, Position, int, int], None],
    keyboard,
    mouse,
    slot1_pos: Position,
    slot2_pos: Position,
    timings: Dict[str, int],
    stop_check: Callable[[], bool],
    log: Callable[[str], None] = print,
) -> None:
    """Run the Quick Dupe Items macro sequence.

    Steps:
    0) Open inventory (Tab)
    1) Split item in quick slot 1 → quick slot 2 (Alt + LMB drag)
    2) Release LMB + Alt
    3) Close inventory (Tab)
    4) Hold Q, press quick slot key (3)
    5) Open inventory (Tab)
    6) Move item from quick slot 1 → quick slot 2 (drag & drop)
    7) Split item in quick slot 2 → quick slot 1 (Alt + LMB drag)
    8) Close inventory (Tab)
    9) Spam left mouse button (max clicks)
    """
    if not slot1_pos or not slot2_pos:
        raise ValueError("Quick slot positions are not set")

    tab_hold = int(timings.get("tab_hold", 50))
    inv_delay = int(timings.get("inv_delay", 120))
    action_delay = int(timings.get("action_delay", 50))
    split_hold = int(timings.get("split_hold", 40))
    drag_speed = int(timings.get("drag_speed", 8))
    q_delay = int(timings.get("q_delay", 120))
    q_select_delay = int(timings.get("q_select_delay", 120))
    drag_hold = int(timings.get("drag_hold", 20))
    alt_delay = int(timings.get("alt_delay", 20))
    spam_delay = int(timings.get("spam_delay", 25))
    # Support either the short key (used by caller) or the full config key
    spam_max_raw = timings.get("spam_max_clicks", timings.get("quick_items_spam_max_clicks", 10))
    try:
        spam_max_clicks = max(0, int(float(spam_max_raw)))
    except Exception:
        spam_max_clicks = 0

    def _stop() -> bool:
        return stop_check()

    def _open_inventory() -> None:
        keyboard.press(Key.tab)
        vsleep(tab_hold)
        keyboard.release(Key.tab)
        vsleep(inv_delay)
        vsleep(action_delay)

    def _close_inventory() -> None:
        keyboard.press(Key.tab)
        vsleep(tab_hold)
        keyboard.release(Key.tab)
        vsleep(action_delay)

    def _drag(start: Position, end: Position, use_alt: bool) -> None:
        if use_alt:
            keyboard.press(Key.alt)
            vsleep(alt_delay)
        _set_mouse_pos(start)
        vsleep(action_delay)
        mouse.press(MouseButton.left)
        vsleep(split_hold if use_alt else drag_hold)
        curved_drag(start, end, 25, drag_speed)
        mouse.release(MouseButton.left)
        if use_alt:
            vsleep(action_delay)
            keyboard.release(Key.alt)

    def _set_mouse_pos(pos: Position) -> None:
        """Force mouse position using both pynput and WinAPI for locked cursors."""
        x, y = int(pos[0]), int(pos[1])
        try:
            mouse.position = (x, y)
        except Exception:
            pass
        try:
            ctypes.windll.user32.SetCursorPos(x, y)
        except Exception:
            pass

    # Clean input state before starting
    mouse.release(MouseButton.left)
    mouse.release(MouseButton.right)
    keyboard.release(Key.tab)
    keyboard.release(Key.alt)
    keyboard.release("q")

    log(f"[QD-ITEMS] Slot1={slot1_pos} Slot2={slot2_pos}")
    # # 1-2) Open inventory and split slot1 -> slot2
    _open_inventory()
    if _stop():
        return
    # 1-2) Split slot1 -> slot2
    _drag(slot1_pos, slot2_pos, use_alt=True)
    if _stop():
        return

    # 3) Close inventory
    _close_inventory()
    if _stop():
        return

    # 4) Hold Q, press quick slot key (3)
    keyboard.press("q")
    vsleep(q_delay)
    keyboard.press("3")
    vsleep(30)
    keyboard.release("3")
    vsleep(q_select_delay)
    keyboard.release("q")
    vsleep(action_delay)

    if _stop():
        return

    # 5) Open inventory
    _open_inventory()
    if _stop():
        return

    # 6) Move item from slot1 -> slot2
    _drag(slot1_pos, slot2_pos, use_alt=False)
    if _stop():
        return

    # 7) Split item from slot2 -> slot1
    _drag(slot2_pos, slot1_pos, use_alt=True)
    if _stop():
        return

    # 8) Close inventory
    _close_inventory()
    if _stop():
        return

    # 9) Spam left mouse button
    log(f"[QD-ITEMS] spam_max_clicks raw={spam_max_raw} parsed={spam_max_clicks}")
    clicks_done = 0
    for _ in range(spam_max_clicks):
        if _stop():
            break
        mouse.press(MouseButton.left)
        vsleep(spam_delay)
        mouse.release(MouseButton.left)
        vsleep(spam_delay)
        clicks_done += 1

    log(f"[QD-ITEMS] Spam clicks: {clicks_done}/{spam_max_clicks}")

    log("[QD-ITEMS] Done")

import keyboard
import subprocess
import ctypes
import sys
import threading
import json
import os
import time
import hashlib
import random
import string
import uuid
import tkinter as tk
from tkinter import ttk, filedialog
import logging

# =============================================================================
# OBFUSCATION FEATURES (opt-in: requires "obfuscate" file next to exe)
# NOTE IF YOU SEE THIS, AND YOU TOOK THE TIME TO READ THE CODE AND
# LEARN ABOUT THE OBFUSCATE FEATURE, PLEASE DO NOT MENTION IT IN THE CHAT
# INSTEAD, SIMPLY UTILIZE IT IF YOU WISH, WHILE NOTING THAT IN THE WORLD
# OF CAT AND MOUSE THAT IS EXPLOITS VS ANTICHEATS, AN ACT TO AVOID DETECTION
# CAN BE THE CATALYST THAT CAUSES DETECTION ITSELF, SUCH IS LIFE
# USING ANY EXPLOIT IN ANY WAY IS ALWAYS A RISK.
#                              -LOVE, 
#                               KILLINMESMALLS/YOUSTAYGOLD/YOUR FATHER
# =============================================================================
# Unique build identifier - generated fresh each build by build.py
BUILD_ID = "__BUILD_ID_PLACEHOLDER__"

def _check_obfuscation_enabled():
    """Check if obfuscation is enabled by looking for 'obfuscate' file next to exe"""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.exists(os.path.join(exe_dir, "obfuscate"))

OBFUSCATION_ENABLED = _check_obfuscation_enabled()

VERSION = "1.5.2"

# Generate random app name (8-18 chars) if obfuscation enabled, otherwise use default
if OBFUSCATION_ENABLED:
    _name_length = random.randint(8, 18)
    _random_name = ''.join(random.choices(string.ascii_letters, k=_name_length))
    APP_NAME = f"{_random_name} {VERSION}"
else:
    _random_name = "QD"
    APP_NAME = f"QD {VERSION}"

def rename_self_and_restart():
    """Rename the running EXE to match the random app name.
    Only runs when obfuscation is enabled and running as frozen exe."""
    if not OBFUSCATION_ENABLED:
        return False

    # Only works for frozen exe, not script
    if not getattr(sys, 'frozen', False):
        return False

    current_exe = sys.executable
    current_dir = os.path.dirname(current_exe)
    marker_file = os.path.join(current_dir, "DELETETOCHANGEID")

    # If marker exists, already renamed - skip
    if os.path.exists(marker_file):
        return False

    # Use the random name generated for APP_NAME
    new_name = f"{_random_name}.exe"
    new_path = os.path.join(current_dir, new_name)

    try:
        import shutil
        # Copy to new name
        shutil.copy2(current_exe, new_path)

        # Create marker file so it won't rename again
        with open(marker_file, 'w') as f:
            f.write(new_name)

        # Launch the new exe
        subprocess.Popen([new_path] + sys.argv[1:])

        print(f"[OBFUS] Created: {new_name}")
        print(f"[OBFUS] Delete 'DELETETOCHANGEID' to generate new name.")

        # Exit this instance
        sys.exit(0)

    except Exception as e:
        print(f"[OBFUS] Rename failed: {e}")
        return False

    return True

# Setup logging to file
LOG_FILE = os.path.join(os.environ.get('APPDATA', '.'), "QuickDupe", "debug.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("QuickDupe")
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Button as MouseButton, Controller as MouseController

# pynput controllers
pynput_keyboard = KeyboardController()
pynput_mouse = MouseController()

# Packet drop via WinDivert (lazy loaded to avoid network interference on startup)
_pydivert = None  # Lazy loaded
_handle = None
_on = False

def start_packet_drop(outbound=True, inbound=True):
    """DROP PACKETS NOW"""
    global _handle, _on, _pydivert
    if _on:
        return

    # Lazy load pydivert only when needed
    if _pydivert is None:
        import pydivert
        _pydivert = pydivert

    # Match Clumsy's exact filter syntax
    if outbound and inbound:
        filt = "outbound or inbound"  # Clumsy's exact filter
    elif outbound:
        filt = "outbound"
    else:
        filt = "inbound"

    try:
        _handle = _pydivert.WinDivert(filt)
        _handle.open()
        _on = True
        threading.Thread(target=_drop_loop, daemon=True).start()
        time.sleep(0.015)  # Match Clumsy's keypress toggle delay
    except:
        _on = False
        _handle = None

def _drop_loop():
    global _on
    while _on:
        try:
            if _handle:
                _handle.recv()  # recv but don't send = drop
            else:
                break
        except:
            break
    _on = False

def stop_packet_drop():
    """STOP DROPPING NOW"""
    global _handle, _on
    if not _on:
        return
    # Close handle FIRST to unblock recv(), then set flag
    h = _handle
    _handle = None
    _on = False
    if h:
        try:
            h.close()
        except:
            pass
    time.sleep(0.05)  # Give thread time to exit

def is_dropping():
    return _on

# Tamper packet functionality
_tamper_handle = None
_tamper_on = False
_tamper_patterns = [0x64, 0x13, 0x88, 0x40, 0x1F, 0xA0, 0xAA, 0x55]

def start_packet_tamper(outbound=True, inbound=True):
    """Start tampering packets - corrupt data but still send"""
    global _tamper_handle, _tamper_on, _pydivert
    if _tamper_on:
        return

    # Lazy load pydivert only when needed
    if _pydivert is None:
        import pydivert
        _pydivert = pydivert

    if outbound and inbound:
        filt = "outbound or inbound"
    elif outbound:
        filt = "outbound"
    else:
        filt = "inbound"

    try:
        _tamper_handle = _pydivert.WinDivert(filt)
        _tamper_handle.open()
        _tamper_on = True
        threading.Thread(target=_tamper_loop, daemon=True).start()
        print(f"[TAMPER] Started tampering packets ({filt})")
    except Exception as e:
        print(f"[TAMPER] Failed to start: {e}")
        _tamper_on = False
        _tamper_handle = None

def _tamper_loop():
    global _tamper_on
    while _tamper_on and _tamper_handle:
        try:
            packet = _tamper_handle.recv()
            if packet and packet.payload:
                # Tamper the payload data
                payload = bytearray(packet.payload)
                for i in range(len(payload)):
                    payload[i] ^= _tamper_patterns[i % 8]
                packet.payload = bytes(payload)
                # pydivert auto-recalculates checksums
            _tamper_handle.send(packet)
        except:
            break

def stop_packet_tamper():
    """Stop tampering packets"""
    global _tamper_handle, _tamper_on
    if not _tamper_on:
        return
    _tamper_on = False
    if _tamper_handle:
        try:
            _tamper_handle.close()
        except:
            pass
        _tamper_handle = None
    print("[TAMPER] Stopped")

def is_tampering():
    return _tamper_on

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

CONFIG_FILE = os.path.join(os.environ.get('APPDATA', '.'), "QuickDupe", "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


class QuickDupeApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("442x800")
        self.root.resizable(False, True)  # Allow vertical resize
        self.root.overrideredirect(True)  # Remove Windows title bar

        # Disable tkinter bell sound (prevents beeps during macros)
        self.root.bell = lambda: None
        self.root.bind('<Key>', lambda e: None)  # Suppress key event beeps

        # Force show in taskbar despite overrideredirect
        self.root.after(10, self._fix_taskbar)

        # Dark mode colors (dark greys)
        self.colors = {
            'bg': '#1e1e1e',
            'bg_light': '#2d2d2d',
            'accent': '#3c3c3c',
            'text': '#e0e0e0',
            'text_dim': '#808080',
            'highlight': '#e94560',
            'success': '#00d26a',
            'warning': '#ff9f1c'
        }

        # Apply dark theme
        self.root.configure(bg=self.colors['bg'])
        self.setup_dark_theme()

        # Set AppUserModelID for Windows taskbar icon
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('QuickDupe.QuickDupe.1')
        except:
            pass

        # Set window icon
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            png_path = os.path.join(base_path, "icon.png")
            ico_path = os.path.join(base_path, "icon.ico")
            if os.path.exists(png_path):
                self.icon_image = tk.PhotoImage(file=png_path)
                self.root.wm_iconphoto(True, self.icon_image)
            elif os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except:
            pass

        self.config = load_config()

        # Restore window position if saved and reasonable
        saved_x = self.config.get("window_x")
        saved_y = self.config.get("window_y")
        if saved_x is not None and saved_y is not None:
            # Check if position is on screen (reasonable)
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            if 0 <= saved_x < screen_w - 100 and 0 <= saved_y < screen_h - 100:
                self.root.geometry(f"+{saved_x}+{saved_y}")

        # State
        self.triggernade_hotkey_registered = None
        self.disconnected = False
        self.triggernade_running = False
        self.triggernade_stop = False
        self.triggernade_m1_count = 13  # ~13 M1s before reconnect
        self.triggernade_dc_delay = 0.050  # Delay before disconnect (seconds)
        self.triggernade_run_count = 0  # Track runs for randomizing delay
        self.quickdrop_running = False
        self.quickdrop_stop = False
        self.quickdrop_hotkey_registered = None
        self.recording_quickdrop = False
        self.mine_running = False
        self.mine_stop = False
        self.mine_hotkey_registered = None
        self.espam_running = False
        self.espam_stop = False
        self.espam_hotkey_registered = None
        self.escape_hotkey_registered = None
        # Stop All state
        self.recording_stop = False
        # Quick disconnect state
        self.test_disconnected = False
        self.tampering = False
        self.dc_both_hotkey_registered = None
        self.dc_outbound_hotkey_registered = None
        self.dc_inbound_hotkey_registered = None
        self.tamper_hotkey_registered = None
        self.recording_dc_both = False
        self.recording_dc_outbound = False
        self.recording_dc_inbound = False
        self.recording_tamper = False
        self.recording_triggernade = False
        self.recording_mine = False
        self.recording_espam = False
        self.recording_drag = False
        self._recording_previous_value = None  # Store previous value for ESC cancel
        self._drag_recording_cancelled = False  # For ESC cancel of drag recordings
        self._mine_recording_cancelled = False  # For ESC cancel of mine recordings
        self.drag_mouse_listener = None
        self.listening = True  # Always listening

        # Locks to prevent race conditions in hotkey handlers
        self._mine_lock = threading.Lock()
        self._triggernade_lock = threading.Lock()
        self._quickdrop_lock = threading.Lock()
        self._espam_lock = threading.Lock()

        # Overlay
        self.overlay_window = None
        self.overlay_hide_id = None

        # Window handle for minimize (set in _fix_taskbar)
        self.hwnd = None

        # Tray icon
        self.tray_icon = None

        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _add_tooltip(self, widget, text):
        """Add hover tooltip to a widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_attributes('-topmost', True)
            tooltip.configure(bg='#333333')
            label = tk.Label(tooltip, text=text, justify='left', bg='#333333', fg='#e0e0e0',
                           relief='solid', borderwidth=1, padx=8, pady=6, font=('Segoe UI', 9))
            label.pack()
            tooltip.update_idletasks()

            # Smart positioning - flip to left if near right edge
            tip_width = tooltip.winfo_width()
            screen_width = tooltip.winfo_screenwidth()
            x = event.x_root + 20
            if x + tip_width > screen_width:
                x = event.x_root - tip_width - 10
            tooltip.wm_geometry(f"+{x}+{event.y_root + 20}")
            widget._tooltip = tooltip

        def hide_tooltip(event):
            if hasattr(widget, '_tooltip') and widget._tooltip:
                widget._tooltip.destroy()
                widget._tooltip = None

        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def vary(self, ms):
        """Apply random variance to a single timing value (in ms). Returns ms."""
        variance_pct = self.timing_variance_var.get()
        if variance_pct == 0:
            return ms
        max_delta = ms * variance_pct / 100.0
        delta = random.uniform(-max_delta, max_delta)
        return max(1, ms + delta)  # Never go below 1ms

    def vsleep(self, ms):
        """Sleep for ms with variance applied. Checks stop flags every 50ms for responsiveness."""
        total_ms = self.vary(ms)
        chunk_ms = 50  # Check every 50ms for stop signals
        elapsed = 0
        while elapsed < total_ms:
            # Check all stop flags
            if self.mine_stop or self.triggernade_stop or self.espam_stop:
                return  # Exit sleep early if any stop requested
            sleep_time = min(chunk_ms, total_ms - elapsed)
            time.sleep(sleep_time / 1000.0)
            elapsed += sleep_time

    def vary_balanced(self, ms, count):
        """Generate 'count' delays that each vary but sum to exactly ms*count.
        This makes loops look human while keeping total timing identical."""
        variance_pct = self.timing_variance_var.get()
        if variance_pct == 0 or count <= 1:
            return [ms] * count

        # Generate random variations
        max_delta = ms * variance_pct / 100.0
        deltas = [random.uniform(-max_delta, max_delta) for _ in range(count)]

        # Adjust so they sum to zero (balanced)
        avg_delta = sum(deltas) / count
        deltas = [d - avg_delta for d in deltas]

        # Apply to base timing, ensure minimum 1ms
        return [max(1, ms + d) for d in deltas]

    def curved_drag(self, start, end, steps=20, step_delay=5):
        """Perform a drag from start to end with a randomized curved path"""
        import random
        import math

        start_x, start_y = start
        end_x, end_y = end
        dx = end_x - start_x
        dy = end_y - start_y

        # Random curve offset perpendicular to the path
        # Magnitude is 5-15% of the path length
        path_length = math.sqrt(dx*dx + dy*dy)
        curve_magnitude = path_length * random.uniform(0.05, 0.15)
        # Random direction (left or right of path)
        curve_sign = random.choice([-1, 1])
        # Perpendicular vector (normalized)
        if path_length > 0:
            perp_x = -dy / path_length * curve_magnitude * curve_sign
            perp_y = dx / path_length * curve_magnitude * curve_sign
        else:
            perp_x, perp_y = 0, 0

        # Move mouse through curved path using quadratic bezier
        for i in range(steps + 1):
            t = i / steps
            # Quadratic bezier: P = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
            # P0 = start, P2 = end, P1 = midpoint + perpendicular offset
            mid_x = (start_x + end_x) / 2 + perp_x
            mid_y = (start_y + end_y) / 2 + perp_y

            x = (1-t)**2 * start_x + 2*(1-t)*t * mid_x + t**2 * end_x
            y = (1-t)**2 * start_y + 2*(1-t)*t * mid_y + t**2 * end_y

            # Add tiny random jitter
            jitter = random.uniform(-2, 2)
            x += jitter
            y += jitter

            pynput_mouse.position = (int(x), int(y))
            self.vsleep(step_delay)

    def _fix_taskbar(self):
        """Make window show in taskbar despite overrideredirect"""
        # Constants
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        SWP_FRAMECHANGED = 0x0020
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOZORDER = 0x0004
        HWND_NOTOPMOST = -2

        # Ensure window is fully created
        self.root.update()

        # Try multiple methods to get the window handle
        try:
            # Method 1: wm_frame() returns hex string like "0x12345"
            frame = self.root.wm_frame()
            if frame:
                hwnd = int(frame, 16)
            else:
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        except:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())

        if not hwnd:
            hwnd = self.root.winfo_id()

        self.hwnd = hwnd  # Save for minimize
        print(f"[TASKBAR] Window handle: {hwnd} (0x{hwnd:x})")

        # Get and modify extended style
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        print(f"[TASKBAR] Current style: 0x{style:x}")

        # Remove TOOLWINDOW flag, add APPWINDOW flag
        new_style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        print(f"[TASKBAR] New style: 0x{new_style:x}")

        result = ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        print(f"[TASKBAR] SetWindowLongW result: {result}")

        # Force Windows to update the window frame
        ctypes.windll.user32.SetWindowPos(
            hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED
        )

        # Hide and show to force taskbar refresh
        self.root.withdraw()
        self.root.after(100, self._show_window)

    def _show_window(self):
        """Show window after taskbar fix"""
        self.root.deiconify()
        self.root.update()

    def minimize_window(self):
        """Minimize window using Windows API (works with overrideredirect)"""
        if self.hwnd:
            SW_MINIMIZE = 6
            ctypes.windll.user32.ShowWindow(self.hwnd, SW_MINIMIZE)
        else:
            # Fallback - just hide it
            self.root.withdraw()

    def minimize_to_tray(self):
        """Minimize to system tray"""
        # Don't create multiple tray icons
        if self.tray_icon:
            return
        self.root.withdraw()
        self._create_tray_icon()

    def _create_tray_icon(self):
        """Create system tray icon"""
        try:
            import pystray
            from PIL import Image

            # Load icon
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            icon_path = os.path.join(base_path, "icon.png")
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
            else:
                # Create a simple icon if file not found
                image = Image.new('RGB', (64, 64), color='#e94560')

            menu = pystray.Menu(
                pystray.MenuItem("Show", self._restore_from_tray, default=True),
                pystray.MenuItem("Exit", self._exit_from_tray)
            )

            self.tray_icon = pystray.Icon(APP_NAME, image, APP_NAME, menu)
            # Run in thread so it doesn't block
            import threading
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except ImportError:
            # pystray not available, just minimize normally
            print("[TRAY] pystray not installed, using normal minimize")
            self.minimize_window()

    def _restore_from_tray(self, icon=None, item=None):
        """Restore window from tray"""
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.after(0, self._do_restore)

    def _do_restore(self):
        """Actually restore the window (must be called from main thread)"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _exit_from_tray(self, icon=None, item=None):
        """Exit from tray"""
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.after(0, self.on_close)

    def setup_dark_theme(self):
        """Configure ttk styles for dark mode"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors
        style.configure('.', background=self.colors['bg'], foreground=self.colors['text'])
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['text'])
        style.configure('TButton', background=self.colors['accent'], foreground=self.colors['text'],
                        borderwidth=0, relief='flat', focuscolor='')
        style.map('TButton', background=[('active', self.colors['highlight'])])
        style.configure('TCheckbutton', background=self.colors['bg'], foreground=self.colors['text'],
                        indicatorbackground='#404040', indicatorforeground='white',
                        indicatorsize=16)
        style.map('TCheckbutton', background=[('active', self.colors['bg'])])
        style.configure('TEntry', fieldbackground=self.colors['bg_light'], foreground=self.colors['text'],
                        borderwidth=0, relief='flat', padding=2)
        style.configure('TCombobox', fieldbackground='#2d2d2d', background='#2d2d2d',
                        foreground='#e0e0e0', arrowcolor='#e0e0e0')
        style.map('TCombobox', fieldbackground=[('readonly', '#2d2d2d')],
                  selectbackground=[('readonly', '#404040')],
                  selectforeground=[('readonly', '#e0e0e0')])
        self.root.option_add('*TCombobox*Listbox.background', '#2d2d2d')
        self.root.option_add('*TCombobox*Listbox.foreground', '#e0e0e0')
        self.root.option_add('*TCombobox*Listbox.selectBackground', '#404040')
        self.root.option_add('*TCombobox*Listbox.selectForeground', '#e0e0e0')
        style.configure('TSeparator', background=self.colors['accent'])

        # Scrollbar styling - use 'alt' theme element (no grip lines)
        style.element_create('NoGrip.Scrollbar.thumb', 'from', 'alt')
        style.layout('NoGrip.Vertical.TScrollbar', [
            ('Vertical.Scrollbar.trough', {
                'sticky': 'ns',
                'children': [
                    ('NoGrip.Scrollbar.thumb', {'sticky': 'nswe', 'expand': True})
                ]
            })
        ])
        style.configure('NoGrip.Vertical.TScrollbar',
                        background='#404040',
                        troughcolor='#1e1e1e',
                        borderwidth=0,
                        relief='flat',
                        width=10)
        style.map('NoGrip.Vertical.TScrollbar',
                  background=[('active', '#505050'), ('pressed', '#505050')])

        # Scale (slider) styling - no grip lines, no outlines
        style.configure('TScale',
                        background='#404040',
                        troughcolor=self.colors['bg_light'],
                        sliderlength=20,
                        borderwidth=0,
                        relief='flat',
                        gripcount=0,
                        lightcolor='#404040',
                        darkcolor='#404040',
                        bordercolor='#404040',
                        focuscolor='',
                        highlightthickness=0)
        style.configure('Horizontal.TScale',
                        background='#404040',
                        lightcolor='#404040',
                        darkcolor='#404040',
                        bordercolor='#404040',
                        troughcolor=self.colors['bg_light'])

        # Section header style
        style.configure('Header.TLabel',
                        background=self.colors['bg'],
                        foreground=self.colors['highlight'],
                        font=('Arial', 11, 'bold'))

        # Dim text style
        style.configure('Dim.TLabel',
                        background=self.colors['bg'],
                        foreground=self.colors['text_dim'])

    def build_ui(self):
        # Custom title bar
        title_bar = tk.Frame(self.root, bg=self.colors['bg_light'], height=32)
        title_bar.pack(fill='x', side='top')
        title_bar.pack_propagate(False)

        # Drag functionality (define first so we can use it)
        def start_drag(event):
            self._drag_x = event.x
            self._drag_y = event.y

        def drag(event):
            x = self.root.winfo_x() + event.x - self._drag_x
            y = self.root.winfo_y() + event.y - self._drag_y
            self.root.geometry(f"+{x}+{y}")

        # Icon in title bar
        try:
            if hasattr(self, 'icon_image'):
                # Resize icon for title bar
                w, h = self.icon_image.width(), self.icon_image.height()
                factor = max(1, min(w, h) // 20)
                small_icon = self.icon_image.subsample(factor, factor)
                self.title_icon = small_icon  # Keep reference
                icon_label = tk.Label(title_bar, image=small_icon, bg=self.colors['bg_light'])
                icon_label.pack(side='left', padx=(8, 2))
                icon_label.bind('<Button-1>', start_drag)
                icon_label.bind('<B1-Motion>', drag)
        except:
            pass

        # Title label
        title_label = tk.Label(title_bar, text=APP_NAME, bg=self.colors['bg_light'],
                               fg=self.colors['text'], font=('Arial', 10, 'bold'))
        title_label.pack(side='left', padx=2)


        # Close button (rightmost)
        close_btn = tk.Label(title_bar, text=" ✕ ", bg=self.colors['bg_light'],
                            fg=self.colors['text'], font=('Arial', 12), cursor='hand2')
        close_btn.pack(side='right', padx=2)
        close_btn.bind('<Button-1>', lambda e: self.on_close())
        close_btn.bind('<Enter>', lambda e: close_btn.config(bg=self.colors['highlight']))
        close_btn.bind('<Leave>', lambda e: close_btn.config(bg=self.colors['bg_light']))

        # Minimize to tray button (down triangle) - middle
        tray_btn = tk.Label(title_bar, text=" ▼ ", bg=self.colors['bg_light'],
                           fg=self.colors['text'], font=('Arial', 10), cursor='hand2')
        tray_btn.pack(side='right', padx=2)
        tray_btn.bind('<Button-1>', lambda e: self.minimize_to_tray())
        tray_btn.bind('<Enter>', lambda e: tray_btn.config(bg=self.colors['accent']))
        tray_btn.bind('<Leave>', lambda e: tray_btn.config(bg=self.colors['bg_light']))

        # Minimize button (leftmost)
        min_btn = tk.Label(title_bar, text=" ─ ", bg=self.colors['bg_light'],
                          fg=self.colors['text'], font=('Arial', 12), cursor='hand2')
        min_btn.pack(side='right', padx=2)
        min_btn.bind('<Button-1>', lambda e: self.minimize_window())
        min_btn.bind('<Enter>', lambda e: min_btn.config(bg=self.colors['accent']))
        min_btn.bind('<Leave>', lambda e: min_btn.config(bg=self.colors['bg_light']))

        # Bind drag to title bar and label
        title_bar.bind('<Button-1>', start_drag)
        title_bar.bind('<B1-Motion>', drag)
        title_label.bind('<Button-1>', start_drag)
        title_label.bind('<B1-Motion>', drag)

        # Create main container with scrollbar
        container = ttk.Frame(self.root)
        container.pack(fill='both', expand=True)

        # Canvas for scrolling
        self.canvas = tk.Canvas(container, bg=self.colors['bg'], highlightthickness=0)

        # Custom minimal scrollbar using Canvas (no grip lines, clean look)
        self.scrollbar_canvas = tk.Canvas(container, width=10, bg='#1e1e1e', highlightthickness=0, bd=0)
        self.scrollbar_thumb = None
        self.scrollbar_dragging = False
        self.scrollbar_drag_start = 0

        def update_scrollbar(*args):
            if len(args) == 2:
                top, bottom = float(args[0]), float(args[1])
                height = self.scrollbar_canvas.winfo_height()
                thumb_top = int(top * height)
                thumb_bottom = int(bottom * height)
                thumb_height = max(30, thumb_bottom - thumb_top)  # Min thumb size
                self.scrollbar_canvas.delete('thumb')
                self.scrollbar_canvas.create_rectangle(
                    2, thumb_top, 8, thumb_top + thumb_height,
                    fill='#404040', outline='', tags='thumb'
                )

        def on_scrollbar_click(event):
            self.scrollbar_dragging = True
            self.scrollbar_drag_start = event.y

        def on_scrollbar_drag(event):
            if self.scrollbar_dragging:
                delta = event.y - self.scrollbar_drag_start
                self.scrollbar_drag_start = event.y
                height = self.scrollbar_canvas.winfo_height()
                self.canvas.yview_moveto(self.canvas.yview()[0] + delta / height)

        def on_scrollbar_release(event):
            self.scrollbar_dragging = False

        self.scrollbar_canvas.bind('<Button-1>', on_scrollbar_click)
        self.scrollbar_canvas.bind('<B1-Motion>', on_scrollbar_drag)
        self.scrollbar_canvas.bind('<ButtonRelease-1>', on_scrollbar_release)

        # Scrollable frame inside canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=update_scrollbar)

        # Make scrollable frame expand to canvas width so content can center
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind('<Configure>', on_canvas_configure)

        # Force initial width update after window is drawn
        def set_initial_width():
            self.canvas.update_idletasks()
            self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())
        self.root.after(50, set_initial_width)

        # Pack scrollbar and canvas
        self.scrollbar_canvas.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)

        # Enable mousewheel scrolling
        self.canvas.bind_all('<MouseWheel>', lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units'))

        # Build content in scrollable frame
        frame = self.scrollable_frame

        # ===== STAY ON TOP CHECKBOX =====
        self.stay_on_top_var = tk.BooleanVar(value=self.config.get("stay_on_top", False))
        ttk.Checkbutton(frame, text="Stay on top", variable=self.stay_on_top_var, command=self.toggle_stay_on_top).pack(anchor='w', padx=10, pady=5)

        # ===== SHOW OVERLAY CHECKBOX =====
        self.show_overlay_var = tk.BooleanVar(value=self.config.get("show_overlay", True))
        ttk.Checkbutton(frame, text="Show on-screen text", variable=self.show_overlay_var, command=self.save_settings).pack(anchor='w', padx=10, pady=5)

        # ===== TIMING VARIANCE SLIDER =====
        variance_frame = ttk.Frame(frame)
        variance_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(variance_frame, text="Timing variance:").pack(side='left')
        self.timing_variance_var = tk.IntVar(value=self.config.get("timing_variance", 0))
        variance_slider = ttk.Scale(variance_frame, from_=0, to=20, orient='horizontal', variable=self.timing_variance_var, length=100, command=lambda v: self.save_settings())
        variance_slider.pack(side='left', padx=5)
        self.variance_label = ttk.Label(variance_frame, text=f"±{self.timing_variance_var.get()}%")
        self.variance_label.pack(side='left')
        self.timing_variance_var.trace_add('write', lambda *args: self.variance_label.config(text=f"±{self.timing_variance_var.get()}%"))

        # Drag timing values
        self.drag_wait_after = 300    # ms after drop before Tab close

        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # ===== QUICK DISCONNECT SECTION =====
        ttk.Label(frame, text="── Quick Disconnect ──", style='Header.TLabel').pack(pady=(5, 5))

        # DC Both (In+Out) row
        dc_both_frame = ttk.Frame(frame)
        dc_both_frame.pack(fill='x', padx=10, pady=2)
        self.dc_both_btn = tk.Button(dc_both_frame, text="DC BOTH", width=12, bg='#3c3c3c', fg='#e0e0e0',
                                     activebackground='#e94560', activeforeground='white', bd=0,
                                     command=self.toggle_dc_both)
        self.dc_both_btn.pack(side='left')
        ttk.Label(dc_both_frame, text="Hotkey:").pack(side='left', padx=(10, 0))
        self.dc_both_hotkey_var = tk.StringVar(value=self.config.get("dc_both_hotkey", ""))
        self.dc_both_hotkey_entry = tk.Entry(dc_both_frame, textvariable=self.dc_both_hotkey_var, width=10, state="readonly",
                                            bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0', readonlybackground='#2d2d2d')
        self.dc_both_hotkey_entry.pack(side='left', padx=5)
        self.dc_both_record_btn = ttk.Button(dc_both_frame, text="Set", width=4, command=self.start_recording_dc_both)
        self.dc_both_record_btn.pack(side='left')

        # DC Outbound Only row
        dc_out_frame = ttk.Frame(frame)
        dc_out_frame.pack(fill='x', padx=10, pady=2)
        self.dc_outbound_btn = tk.Button(dc_out_frame, text="DC OUTBOUND", width=12, bg='#3c3c3c', fg='#e0e0e0',
                                         activebackground='#e94560', activeforeground='white', bd=0,
                                         command=self.toggle_dc_outbound)
        self.dc_outbound_btn.pack(side='left')
        ttk.Label(dc_out_frame, text="Hotkey:").pack(side='left', padx=(10, 0))
        self.dc_outbound_hotkey_var = tk.StringVar(value=self.config.get("dc_outbound_hotkey", ""))
        self.dc_outbound_hotkey_entry = tk.Entry(dc_out_frame, textvariable=self.dc_outbound_hotkey_var, width=10, state="readonly",
                                                bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0', readonlybackground='#2d2d2d')
        self.dc_outbound_hotkey_entry.pack(side='left', padx=5)
        self.dc_outbound_record_btn = ttk.Button(dc_out_frame, text="Set", width=4, command=self.start_recording_dc_outbound)
        self.dc_outbound_record_btn.pack(side='left')

        # DC Inbound Only row
        dc_in_frame = ttk.Frame(frame)
        dc_in_frame.pack(fill='x', padx=10, pady=2)
        self.dc_inbound_btn = tk.Button(dc_in_frame, text="DC INBOUND", width=12, bg='#3c3c3c', fg='#e0e0e0',
                                        activebackground='#e94560', activeforeground='white', bd=0,
                                        command=self.toggle_dc_inbound)
        self.dc_inbound_btn.pack(side='left')
        ttk.Label(dc_in_frame, text="Hotkey:").pack(side='left', padx=(10, 0))
        self.dc_inbound_hotkey_var = tk.StringVar(value=self.config.get("dc_inbound_hotkey", ""))
        self.dc_inbound_hotkey_entry = tk.Entry(dc_in_frame, textvariable=self.dc_inbound_hotkey_var, width=10, state="readonly",
                                               bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0', readonlybackground='#2d2d2d')
        self.dc_inbound_hotkey_entry.pack(side='left', padx=5)
        self.dc_inbound_record_btn = ttk.Button(dc_in_frame, text="Set", width=4, command=self.start_recording_dc_inbound)
        self.dc_inbound_record_btn.pack(side='left')

        # Tamper button (corrupts packets instead of dropping)
        tamper_frame = ttk.Frame(frame)
        tamper_frame.pack(fill='x', padx=10, pady=2)
        self.tamper_btn = tk.Button(tamper_frame, text="TAMPER", width=12, bg='#3c3c3c', fg='#e0e0e0',
                                    activebackground='#ff8c00', activeforeground='white', bd=0,
                                    command=self.toggle_tamper)
        self.tamper_btn.pack(side='left')
        ttk.Label(tamper_frame, text="Hotkey:").pack(side='left', padx=(10, 0))
        self.tamper_hotkey_var = tk.StringVar(value=self.config.get("tamper_hotkey", ""))
        self.tamper_hotkey_entry = tk.Entry(tamper_frame, textvariable=self.tamper_hotkey_var, width=10, state="readonly",
                                           bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0', readonlybackground='#2d2d2d')
        self.tamper_hotkey_entry.pack(side='left', padx=5)
        self.tamper_record_btn = ttk.Button(tamper_frame, text="Set", width=4, command=self.start_recording_tamper)
        self.tamper_record_btn.pack(side='left')
        tamper_info = ttk.Label(tamper_frame, text=" (?)", foreground='#888888', cursor='hand2')
        tamper_info.pack(side='left')
        self._add_tooltip(tamper_info, "Corrupts packets instead of dropping them.\nCan cause weird behavior instead of full DC.")

        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # ===== TRIGGERNADE SECTION =====
        trig_header = ttk.Frame(frame)
        trig_header.pack(pady=(5, 5))
        ttk.Label(trig_header, text="── Wolfpack/Triggernade Dupe ──", style='Header.TLabel').pack(side='left')
        trig_info = ttk.Label(trig_header, text=" (?)", foreground='#888888', cursor='hand2')
        trig_info.pack(side='left')
        self._add_tooltip(trig_info, "Record drag path from item slot to ground.\n\nMake sure inventory is full of items you're NOT duping (e.g. stacks of 1 ammo).\nFill safe pockets as well.\n\nQuick use slots must be empty EXCEPT item you're duping in first slot.\nEven utility slots must be empty.\n\nThen press Q to bring out wolfpack/triggernade/leaper pulse unit/other grenade and hit hotkey.\n\nTIP: Get it working SINGLE USE first. For auto-repeat, item must roll under your feet\nto be grabbed for looping. Drop piles of 1 of item you're duping around feet as backup copies to grab.\n\nTRIGGERNADES: Start with stack of 3 in first quick use slot - if it fails 2x it keeps going.\nTriggernades are unique: when picked up they return to the same stack.")

        # Triggernade Hotkey row
        trig_hk = ttk.Frame(frame)
        trig_hk.pack(fill='x', padx=10, pady=5)
        ttk.Label(trig_hk, text="Hotkey:").pack(side='left')
        self.triggernade_hotkey_var = tk.StringVar(value=self.config.get("triggernade_hotkey", ""))
        self.triggernade_hotkey_entry = tk.Entry(trig_hk, textvariable=self.triggernade_hotkey_var, width=15, state="readonly",
                                               bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0', readonlybackground='#2d2d2d')
        self.triggernade_hotkey_entry.pack(side='left', padx=5)
        self.triggernade_record_btn = ttk.Button(trig_hk, text="Set", width=6, command=self.start_recording_triggernade)
        self.triggernade_record_btn.pack(side='left', padx=5)

        # Triggernade drag record (works for both Xbox X and drag drop)
        trig_drag_frame = ttk.Frame(frame)
        trig_drag_frame.pack(fill='x', padx=10, pady=2)
        self.trig_drag_btn = ttk.Button(trig_drag_frame, text="Record", width=12, command=self.start_trig_drag_recording)
        self.trig_drag_btn.pack(side='left')
        self.trig_drag_var = tk.StringVar()
        # Load triggernade positions (slot + drop to ground)
        trig_slot = self.config.get("trig_slot_pos", None)
        trig_drop = self.config.get("trig_drop_pos", None)
        self.trig_slot_pos = tuple(trig_slot) if trig_slot else None
        self.trig_drop_pos = tuple(trig_drop) if trig_drop else None
        # Legacy drag positions (kept for compatibility)
        trig_drag_s = self.config.get("trig_drag_start", None)
        trig_drag_e = self.config.get("trig_drag_end", None)
        self.trig_drag_start = tuple(trig_drag_s) if trig_drag_s else None
        self.trig_drag_end = tuple(trig_drag_e) if trig_drag_e else None
        if trig_slot and trig_drop:
            self.trig_drag_var.set(f"Slot:{list(trig_slot)} Drop:{list(trig_drop)}")
        else:
            self.trig_drag_var.set("Not recorded - click Record first")
        ttk.Label(trig_drag_frame, textvariable=self.trig_drag_var, font=("Consolas", 8)).pack(side='left', padx=5)

        # Repeat checkbox
        self.triggernade_repeat_var = tk.BooleanVar(value=self.config.get("triggernade_repeat", False))
        ttk.Checkbutton(frame, text="Auto (loop until pressed again)", variable=self.triggernade_repeat_var, command=self.save_settings).pack(anchor='w', padx=10, pady=5)

        # Q spam checkbox (optional re-equip between cycles)
        self.triggernade_q_spam_var = tk.BooleanVar(value=self.config.get("triggernade_q_spam", False))
        ttk.Checkbutton(frame, text="Q spam between cycles (re-equip)", variable=self.triggernade_q_spam_var, command=self.save_settings).pack(anchor='w', padx=10, pady=2)

        # Triggernade Timings
        # Cook time - THE MOST IMPORTANT TIMING (use same layout as other sliders)
        cook_frame = ttk.Frame(frame)
        cook_frame.pack(fill='x', padx=10, pady=2)
        ttk.Label(cook_frame, text="Cook time:", width=20, anchor='w',
                  font=("Arial", 9, "bold")).pack(side='left')
        self.trig_m1_hold_var = tk.IntVar(value=int(self.config.get("trig_m1_hold", 65)))

        def on_cook_slide(val):
            self.trig_m1_hold_var.set(int(float(val)))
            self.save_settings()

        cook_slider = ttk.Scale(cook_frame, from_=10, to=500, variable=self.trig_m1_hold_var,
                               orient='horizontal', length=100, command=on_cook_slide)
        cook_slider.pack(side='left', padx=5)

        cook_entry = tk.Entry(cook_frame, width=5, justify='center', bd=0, highlightthickness=0,
                             bg='#2d2d2d', fg='#e0e0e0', insertbackground='white')
        cook_entry.pack(side='left')
        cook_entry.insert(0, str(self.trig_m1_hold_var.get()))

        def on_cook_entry(event=None):
            try:
                val = int(cook_entry.get())
                val = max(10, min(10000, val))
                self.trig_m1_hold_var.set(val)
                cook_entry.delete(0, 'end')
                cook_entry.insert(0, str(val))
                self.save_settings()
            except ValueError:
                cook_entry.delete(0, 'end')
                cook_entry.insert(0, str(self.trig_m1_hold_var.get()))

        def on_cook_var_change(*args):
            cook_entry.delete(0, 'end')
            cook_entry.insert(0, str(self.trig_m1_hold_var.get()))

        cook_entry.bind('<Return>', on_cook_entry)
        cook_entry.bind('<FocusOut>', on_cook_entry)
        self.trig_m1_hold_var.trace_add('write', on_cook_var_change)
        ttk.Label(cook_frame, text="ms").pack(side='left')
        self.create_slider(frame, "M2 hold time:", "trig_m2_hold", 51, 10, 500, "ms")
        self.create_slider(frame, "Drag speed:", "trig_drag_speed", 8, 3, 20, "ms/step")
        self.create_slider(frame, "Delay before DC:", "trig_dc_delay", 10, 0, 200, "ms")
        self.create_slider(frame, "M1s while DC'd:", "trig_dc_throws", 10, 1, 30, "")
        self.create_slider(frame, "Time between M1s:", "trig_throw_delay", 100, 10, 500, "ms")
        self.create_slider(frame, "Reconnect after M1 #:", "trig_reconnect_after", 1, 1, 20, "")
        self.create_slider(frame, "Wait before E spam:", "wait_before_espam", 0, 0, 2000, "ms")
        self.create_slider(frame, "E spam duration:", "espam_duration", 250, 0, 5000, "ms")
        self.create_slider(frame, "M1s before E interweave:", "trig_m1_before_interweave", 1, 0, 20, "")
        self.create_slider(frame, "Wait before next cycle:", "wait_before_cycle", 100, 0, 2000, "ms")

        # Wolfpack loop settings header
        ttk.Label(frame, text="─ Wolfpack Loop Settings ─", font=("Arial", 9, "bold")).pack(pady=(10, 5))
        self.create_slider(frame, "Loop M1 hold:", "wolfpack_m1_hold", 20, 10, 200, "ms")
        self.create_slider(frame, "Loop M1 gap:", "wolfpack_m1_gap", 20, 10, 200, "ms")
        self.create_slider(frame, "Loop DC hold:", "wolfpack_dc_hold", 20, 10, 500, "ms")
        self.create_slider(frame, "Loop DC gap:", "wolfpack_dc_gap", 600, 100, 3000, "ms")

        trig_btn_frame = ttk.Frame(frame)
        trig_btn_frame.pack(pady=5)
        ttk.Button(trig_btn_frame, text="Reset Defaults", command=self.reset_triggernade_defaults).pack(side='left', padx=2)
        ttk.Button(trig_btn_frame, text="Export", width=7, command=self.export_triggernade).pack(side='left', padx=2)
        ttk.Button(trig_btn_frame, text="Import", width=7, command=self.import_triggernade).pack(side='left', padx=2)
        self.triggernade_status_var = tk.StringVar(value="Ready")
        self.triggernade_status_label = ttk.Label(frame, textvariable=self.triggernade_status_var, style='Dim.TLabel')
        self.triggernade_status_label.pack(pady=5)

        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # ===== QUICK DROP (NO DC) SECTION =====
        qd_header = ttk.Frame(frame)
        qd_header.pack(pady=(5, 5))
        ttk.Label(qd_header, text="── Quick Drop (No DC) ──", style='Header.TLabel').pack(side='left')
        qd_info = ttk.Label(qd_header, text=" (?)", foreground='#888888', cursor='hand2')
        qd_info.pack(side='left')
        self._add_tooltip(qd_info, "Same as triggernade but NO DISCONNECT.\nUses right-click context menu drop instead of drag.\nRight-click on item → Left-click 'Drop to Ground'.\nSuper fast, almost instant.")

        # Quick Drop Hotkey row
        qd_hk = ttk.Frame(frame)
        qd_hk.pack(fill='x', padx=10, pady=5)
        ttk.Label(qd_hk, text="Hotkey:").pack(side='left')
        self.quickdrop_hotkey_var = tk.StringVar(value=self.config.get("quickdrop_hotkey", ""))
        self.quickdrop_hotkey_entry = tk.Entry(qd_hk, textvariable=self.quickdrop_hotkey_var, width=15, state="readonly",
                                         bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0', readonlybackground='#2d2d2d')
        self.quickdrop_hotkey_entry.pack(side='left', padx=5)
        self.quickdrop_record_btn = ttk.Button(qd_hk, text="Set", width=6, command=self.start_recording_quickdrop)
        self.quickdrop_record_btn.pack(side='left', padx=5)

        # Quick Drop position record
        qd_pos_frame = ttk.Frame(frame)
        qd_pos_frame.pack(fill='x', padx=10, pady=2)
        self.quickdrop_pos_btn = ttk.Button(qd_pos_frame, text="Record Pos", width=12, command=self.start_quickdrop_pos_recording)
        self.quickdrop_pos_btn.pack(side='left')
        self.quickdrop_pos_var = tk.StringVar()
        # Load quick drop positions (right-click pos + left-click drop pos)
        qd_rclick = self.config.get("quickdrop_rclick_pos", [0, 0])
        qd_lclick = self.config.get("quickdrop_lclick_pos", [0, 0])
        self.quickdrop_rclick_pos = tuple(qd_rclick)
        self.quickdrop_lclick_pos = tuple(qd_lclick)
        self.quickdrop_pos_var.set(f"R:{qd_rclick} L:{qd_lclick}")
        ttk.Label(qd_pos_frame, textvariable=self.quickdrop_pos_var, font=("Consolas", 8)).pack(side='left', padx=5)

        # Repeat checkbox
        self.quickdrop_repeat_var = tk.BooleanVar(value=self.config.get("quickdrop_repeat", False))
        ttk.Checkbutton(frame, text="Auto (loop until pressed again)", variable=self.quickdrop_repeat_var, command=self.save_settings).pack(anchor='w', padx=10, pady=5)

        # Quick Drop status
        self.quickdrop_status_var = tk.StringVar(value="Ready")
        self.quickdrop_status_label = ttk.Label(frame, textvariable=self.quickdrop_status_var, style='Dim.TLabel')
        self.quickdrop_status_label.pack(pady=5)

        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # ===== MINE DUPE SECTION =====
        mine_header = ttk.Frame(frame)
        mine_header.pack(pady=(5, 5))
        ttk.Label(mine_header, text="── Mine Dupe ──", style='Header.TLabel').pack(side='left')
        mine_info = ttk.Label(mine_header, text=" (?)", foreground='#888888', cursor='hand2')
        mine_info.pack(side='left')
        self._add_tooltip(mine_info, "Record drag path from mine slot to ground.\nIf using SURVIVOR AUGMENT: record drag from UTILITY SLOT or it won't work.\n\nCOOK TIME: The use circle should be ALMOST full when inventory opens.\n- If mine deploys before/while opening inventory: reduce cook time\n- Make small adjustments until circle is mostly full on open\n\nDELAY BEFORE DC: Make very light adjustments if still not working.\n\nRECONNECT TO CLICK: If mine drops from inventory but duplicate doesn't place,\nadjust this timing in small increments either direction. Watch for consistency.\n\nTIP: Get it working SINGLE USE first. For auto-repeat, item must roll under your feet\nto be grabbed for looping. Drop piles of 1 of item you're duping around feet as backup copies to grab.")

        # Mine Hotkey row
        mine_hk = ttk.Frame(frame)
        mine_hk.pack(fill='x', padx=10, pady=5)
        ttk.Label(mine_hk, text="Hotkey:").pack(side='left')
        self.mine_hotkey_var = tk.StringVar(value=self.config.get("mine_hotkey", ""))
        self.mine_hotkey_entry = tk.Entry(mine_hk, textvariable=self.mine_hotkey_var, width=15, state="readonly",
                                         bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0', readonlybackground='#2d2d2d')
        self.mine_hotkey_entry.pack(side='left', padx=5)
        self.mine_record_btn = ttk.Button(mine_hk, text="Set", width=6, command=self.start_recording_mine)
        self.mine_record_btn.pack(side='left', padx=5)

        self.mine_repeat_var = tk.BooleanVar(value=self.config.get("mine_repeat", False))
        ttk.Checkbutton(frame, text="Auto-repeat", variable=self.mine_repeat_var, command=self.save_settings).pack(anchor='w', padx=10, pady=2)

        # Mine drag/slot record
        mine_drag_frame = ttk.Frame(frame)
        mine_drag_frame.pack(fill='x', padx=10, pady=5)
        self.mine_drag_btn = ttk.Button(mine_drag_frame, text="Record", width=12, command=self.start_mine_drag_recording)
        self.mine_drag_btn.pack(side='left')
        self.mine_drag_var = tk.StringVar()
        # Load mine positions (slot + drop to ground)
        mine_slot = self.config.get("mine_slot_pos", [3032, 1236])
        mine_drop = self.config.get("mine_drop_pos", [3171, 1593])
        self.mine_slot_pos = tuple(mine_slot)
        self.mine_drop_pos = tuple(mine_drop)
        # Legacy drag positions (kept for compatibility)
        self.mine_drag_start = tuple(self.config.get("mine_drag_start", [3032, 1236]))
        self.mine_drag_end = tuple(self.config.get("mine_drag_end", [3171, 1593]))
        self.mine_drag_var.set(f"Slot:{mine_slot} Drop:{mine_drop}")
        ttk.Label(mine_drag_frame, textvariable=self.mine_drag_var, font=("Consolas", 8)).pack(side='left', padx=10)

        # Mine Timings
        ttk.Label(frame, text="Timings:", font=("Arial", 9, "bold")).pack(anchor='w', padx=10, pady=(5, 2))

        # Cook time with extended range (slider 500, entry 10000)
        mine_cook_frame = ttk.Frame(frame)
        mine_cook_frame.pack(fill='x', padx=10, pady=2)
        ttk.Label(mine_cook_frame, text="Cook time:", width=20, anchor='w', font=("Arial", 9, "bold")).pack(side='left')
        self.mine_cook_var = tk.IntVar(value=int(self.config.get("mine_cook", 236)))

        def on_mine_cook_slide(val):
            self.mine_cook_var.set(int(float(val)))
            self.save_settings()

        mine_cook_slider = ttk.Scale(mine_cook_frame, from_=10, to=5000, variable=self.mine_cook_var,
                                     orient='horizontal', length=100, command=on_mine_cook_slide)
        mine_cook_slider.pack(side='left', padx=5)

        mine_cook_entry = tk.Entry(mine_cook_frame, width=6, justify='center', bd=0, highlightthickness=0,
                                   bg='#2d2d2d', fg='#e0e0e0', insertbackground='white')
        mine_cook_entry.pack(side='left')
        mine_cook_entry.insert(0, str(self.mine_cook_var.get()))

        def on_mine_cook_entry(event=None):
            try:
                val = int(mine_cook_entry.get())
                val = max(10, min(10000, val))
                self.mine_cook_var.set(val)
                mine_cook_entry.delete(0, 'end')
                mine_cook_entry.insert(0, str(val))
                self.save_settings()
            except ValueError:
                mine_cook_entry.delete(0, 'end')
                mine_cook_entry.insert(0, str(self.mine_cook_var.get()))

        def on_mine_cook_var_change(*args):
            mine_cook_entry.delete(0, 'end')
            mine_cook_entry.insert(0, str(self.mine_cook_var.get()))

        mine_cook_entry.bind('<Return>', on_mine_cook_entry)
        mine_cook_entry.bind('<FocusOut>', on_mine_cook_entry)
        self.mine_cook_var.trace_add('write', on_mine_cook_var_change)
        ttk.Label(mine_cook_frame, text="ms").pack(side='left')

        # Defaults based on YOUR successful recordings
        self.create_slider(frame, "Delay before DC:", "mine_dc_delay", 99, 0, 500, "ms", bold=True)
        self.create_slider(frame, "Drag speed:", "mine_drag_speed", 8, 3, 20, "ms/step")
        self.create_slider(frame, "Pre-close delay:", "mine_pre_close", 100, 0, 2000, "ms")
        self.create_slider(frame, "TAB hold (close):", "mine_tab_hold", 80, 20, 300, "ms")
        self.create_slider(frame, "Close to reconnect:", "mine_close_reconnect", 409, 100, 2000, "ms", bold=True)
        self.create_slider(frame, "Reconnect to click:", "mine_click_delay", 7, 0, 500, "ms", bold=True)
        self.create_slider(frame, "Dupe click hold:", "mine_pickup_hold", 1336, 100, 3000, "ms", bold=True)
        self.create_slider(frame, "Delay before E:", "mine_e_delay", 868, 0, 2000, "ms")
        self.create_slider(frame, "Delay before loop:", "mine_loop_delay", 550, 0, 2000, "ms")

        # Q reselect option
        reselect_frame = ttk.Frame(frame)
        reselect_frame.pack(fill='x', padx=10, pady=5)
        self.mine_reselect_var = tk.BooleanVar(value=self.config.get("mine_reselect", True))
        ttk.Checkbutton(reselect_frame, text="Q to reselect", variable=self.mine_reselect_var, command=self.save_settings).pack(side='left')

        # Q mode: simple tap or recorded radial
        default_q_recording = [
            [1920, 1080], [1920, 1064], [1920, 1046], [1920, 1020], [1920, 982],
            [1920, 949], [1922, 914], [1925, 884], [1928, 852], [1922, 1058],
            [1926, 1035], [1927, 1012], [1930, 993], [1922, 1065], [1924, 1049]
        ]
        self.mine_q_mode_var = tk.StringVar(value=self.config.get("mine_q_mode", "radial"))
        ttk.Radiobutton(reselect_frame, text="Simple tap", variable=self.mine_q_mode_var, value="simple", command=self.save_settings).pack(side='left', padx=(10, 5))
        ttk.Radiobutton(reselect_frame, text="Radial:", variable=self.mine_q_mode_var, value="radial", command=self.save_settings).pack(side='left')

        # Direction picker button - opens compass popup
        self.mine_q_direction_var = tk.StringVar(value=self.config.get("mine_q_direction", "S"))
        self.mine_q_dir_btn = ttk.Button(reselect_frame, text=self.mine_q_direction_var.get(), width=3,
                                         command=self._show_direction_picker)
        self.mine_q_dir_btn.pack(side='left', padx=2)

        # Mouse nudge option (move mouse between loops)
        nudge_frame = ttk.Frame(frame)
        nudge_frame.pack(fill='x', padx=10, pady=5)
        self.mine_nudge_var = tk.BooleanVar(value=self.config.get("mine_nudge", True))
        ttk.Checkbutton(nudge_frame, text="Nudge mouse", variable=self.mine_nudge_var, command=self.save_settings).pack(side='left')
        self.mine_nudge_px_var = tk.IntVar(value=self.config.get("mine_nudge_px", 50))
        nudge_entry = tk.Entry(nudge_frame, textvariable=self.mine_nudge_px_var, width=5, justify='center',
                               bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0')
        nudge_entry.pack(side='left', padx=5)
        nudge_entry.bind('<Return>', lambda e: self.save_settings())
        nudge_entry.bind('<FocusOut>', lambda e: self.save_settings())
        ttk.Label(nudge_frame, text="px right per loop").pack(side='left')

        mine_btn_frame = ttk.Frame(frame)
        mine_btn_frame.pack(pady=5)
        ttk.Button(mine_btn_frame, text="Reset Defaults", command=self.reset_mine_defaults).pack(side='left', padx=2)
        ttk.Button(mine_btn_frame, text="Export", width=7, command=self.export_mine).pack(side='left', padx=2)
        ttk.Button(mine_btn_frame, text="Import", width=7, command=self.import_mine).pack(side='left', padx=2)
        self.mine_status_var = tk.StringVar(value="Ready")
        self.mine_status_label = ttk.Label(frame, textvariable=self.mine_status_var, style='Dim.TLabel')
        self.mine_status_label.pack(pady=5)

        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # ===== RECONNECT MACRO SECTION =====
        reconnect_header = ttk.Frame(frame)
        reconnect_header.pack(pady=(5, 5))
        ttk.Label(reconnect_header, text="── Reconnect Macro ──", style='Header.TLabel').pack(side='left')
        reconnect_info = ttk.Label(reconnect_header, text=" (?)", foreground='#888888', cursor='hand2')
        reconnect_info.pack(side='left')
        self._add_tooltip(reconnect_info, "Record and playback custom reconnect sequence.\nENTER to start, F12 to stop recording.")

        # Hotkey row
        reconnect_hk_frame = ttk.Frame(frame)
        reconnect_hk_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(reconnect_hk_frame, text="Hotkey:").pack(side='left')
        self.reconnect_hotkey_var = tk.StringVar(value=self.config.get("reconnect_hotkey", ""))
        self.reconnect_hotkey_entry = tk.Entry(reconnect_hk_frame, textvariable=self.reconnect_hotkey_var, width=15, state="readonly",
                                               bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0', readonlybackground='#2d2d2d')
        self.reconnect_hotkey_entry.pack(side='left', padx=5)
        self.reconnect_hk_btn = ttk.Button(reconnect_hk_frame, text="Set", width=6, command=self.start_recording_reconnect_hotkey)
        self.reconnect_hk_btn.pack(side='left', padx=5)

        reconnect_btn_frame = ttk.Frame(frame)
        reconnect_btn_frame.pack(pady=5)
        self.reconnect_record_btn = ttk.Button(reconnect_btn_frame, text="Record", width=10, command=self.start_reconnect_recording)
        self.reconnect_record_btn.pack(side='left', padx=2)
        self.reconnect_play_btn = ttk.Button(reconnect_btn_frame, text="Play", width=10, command=self.play_reconnect_macro)
        self.reconnect_play_btn.pack(side='left', padx=2)

        self.reconnect_status_var = tk.StringVar(value="No recording")
        self.reconnect_status_label = ttk.Label(frame, textvariable=self.reconnect_status_var, style='Dim.TLabel')
        self.reconnect_status_label.pack(pady=5)

        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # ===== E-SPAM COLLECTION SECTION =====
        espam_header = ttk.Frame(frame)
        espam_header.pack(pady=(5, 5))
        ttk.Label(espam_header, text="── E-Spam Collection ──", style='Header.TLabel').pack(side='left')
        espam_info = ttk.Label(espam_header, text=" (?)", foreground='#888888', cursor='hand2')
        espam_info.pack(side='left')
        self._add_tooltip(espam_info, "Used to gather already completed mines/triggernades.")

        espam_hk = ttk.Frame(frame)
        espam_hk.pack(fill='x', padx=10, pady=5)
        ttk.Label(espam_hk, text="Hotkey:").pack(side='left')
        self.espam_hotkey_var = tk.StringVar(value=self.config.get("espam_hotkey", ""))
        self.espam_hotkey_entry = tk.Entry(espam_hk, textvariable=self.espam_hotkey_var, width=15, state="readonly",
                                         bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0', readonlybackground='#2d2d2d')
        self.espam_hotkey_entry.pack(side='left', padx=5)
        self.espam_record_btn = ttk.Button(espam_hk, text="Set", width=6, command=self.start_recording_espam)
        self.espam_record_btn.pack(side='left', padx=5)

        # Hold vs Toggle option
        self.espam_hold_mode_var = tk.BooleanVar(value=self.config.get("espam_hold_mode", False))
        ttk.Checkbutton(frame, text="Hold to activate (vs toggle)", variable=self.espam_hold_mode_var,
                        command=self.save_settings).pack(anchor='w', padx=10, pady=2)

        # Time between E spam bursts (in ms)
        self.create_slider(frame, "Time before repeat:", "espam_repeat_delay", 0, 0, 5000, "ms")

        self.espam_status_var = tk.StringVar(value="Ready")
        self.espam_status_label = ttk.Label(frame, textvariable=self.espam_status_var, style='Dim.TLabel')
        self.espam_status_label.pack(pady=5)

        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # ===== HOTKEYS (Minimize) =====
        ttk.Label(frame, text="── Window Hotkeys ──", style='Header.TLabel').pack(pady=(5, 5))

        # Minimize hotkey
        min_hk_frame = ttk.Frame(frame)
        min_hk_frame.pack(fill='x', padx=10, pady=2)
        ttk.Label(min_hk_frame, text="Minimize:").pack(side='left')
        self.minimize_hotkey_var = tk.StringVar(value=self.config.get("minimize_hotkey", ""))
        self.minimize_hotkey_entry = tk.Entry(min_hk_frame, textvariable=self.minimize_hotkey_var, width=10, state="readonly",
                                             bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0', readonlybackground='#2d2d2d')
        self.minimize_hotkey_entry.pack(side='left', padx=5)
        self.minimize_record_btn = ttk.Button(min_hk_frame, text="Set", width=4, command=self.start_recording_minimize)
        self.minimize_record_btn.pack(side='left')
        self.recording_minimize = False

        # Minimize to tray hotkey
        tray_hk_frame = ttk.Frame(frame)
        tray_hk_frame.pack(fill='x', padx=10, pady=2)
        ttk.Label(tray_hk_frame, text="Minimize to Tray:").pack(side='left')
        self.tray_hotkey_var = tk.StringVar(value=self.config.get("tray_hotkey", ""))
        self.tray_hotkey_entry = tk.Entry(tray_hk_frame, textvariable=self.tray_hotkey_var, width=10, state="readonly",
                                         bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0', readonlybackground='#2d2d2d')
        self.tray_hotkey_entry.pack(side='left', padx=5)
        self.tray_record_btn = ttk.Button(tray_hk_frame, text="Set", width=4, command=self.start_recording_tray)
        self.tray_record_btn.pack(side='left')
        self.recording_tray = False

        ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # ===== GLOBAL EXPORT/IMPORT =====
        ttk.Label(frame, text="── All Settings ──", style='Header.TLabel').pack(pady=(5, 5))
        global_btn_frame = ttk.Frame(frame)
        global_btn_frame.pack(pady=5)
        ttk.Button(global_btn_frame, text="Export All", width=10, command=self.export_all_settings).pack(side='left', padx=2)
        ttk.Button(global_btn_frame, text="Import All", width=10, command=self.import_all_settings).pack(side='left', padx=2)

        # ===== RESET ALL =====
        ttk.Button(frame, text="Reset ALL Settings", command=self.reset_all_settings).pack(pady=5)

        # ===== STOP ALL HOTKEY =====
        stop_frame = ttk.Frame(frame)
        stop_frame.pack(fill='x', padx=10, pady=(15, 5))
        ttk.Label(stop_frame, text="Stop All:").pack(side='left')
        self.stop_hotkey_var = tk.StringVar(value=self.config.get("stop_hotkey", "esc"))
        self.stop_hotkey_entry = tk.Entry(stop_frame, textvariable=self.stop_hotkey_var, width=15, state="readonly",
                                          bd=0, highlightthickness=0, bg='#2d2d2d', fg='#e0e0e0', readonlybackground='#2d2d2d')
        self.stop_hotkey_entry.pack(side='left', padx=5)
        self.stop_record_btn = ttk.Button(stop_frame, text="Set", width=6, command=self.start_recording_stop)
        self.stop_record_btn.pack(side='left', padx=5)

        # ===== RESIZE GRIP (bottom of window) =====
        resize_grip = tk.Frame(self.root, bg='#2d2d2d', height=8, cursor='sb_v_double_arrow')
        resize_grip.pack(side='bottom', fill='x')

        def start_resize(event):
            self._resize_start_y = event.y_root
            self._resize_start_height = self.root.winfo_height()

        def do_resize(event):
            delta = event.y_root - self._resize_start_y
            new_height = max(400, self._resize_start_height + delta)  # Min height 400
            self.root.geometry(f"442x{new_height}")

        resize_grip.bind('<Button-1>', start_resize)
        resize_grip.bind('<B1-Motion>', do_resize)


    def create_slider(self, parent, label, config_key, default, min_val, max_val, unit, bold=False, tooltip=None):
        """Create a slider row with label, slider, and editable value entry"""
        row = ttk.Frame(parent)
        row.pack(fill='x', padx=10, pady=2)

        if bold:
            lbl = ttk.Label(row, text=label, width=20, anchor='w', font=('Segoe UI', 9, 'bold'))
        else:
            lbl = ttk.Label(row, text=label, width=20, anchor='w')
        lbl.pack(side='left')

        # Add tooltip if provided
        if tooltip:
            def show_tooltip(event):
                tip = tk.Toplevel(row)
                tip.wm_overrideredirect(True)
                tip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                tip_label = tk.Label(tip, text=tooltip, justify='left', background="#ffffe0",
                                    relief='solid', borderwidth=1, font=("Segoe UI", 8),
                                    wraplength=300)
                tip_label.pack()
                row._tooltip = tip
            def hide_tooltip(event):
                if hasattr(row, '_tooltip'):
                    row._tooltip.destroy()
                    del row._tooltip
            lbl.bind('<Enter>', show_tooltip)
            lbl.bind('<Leave>', hide_tooltip)

        var = tk.IntVar(value=int(self.config.get(config_key, default)))
        setattr(self, f"{config_key}_var", var)

        def on_slide(val):
            var.set(int(float(val)))
            self.save_settings()

        slider = ttk.Scale(row, from_=min_val, to=max_val, variable=var, orient='horizontal', length=100,
                          command=on_slide)
        slider.pack(side='left', padx=5)

        # Editable entry instead of label (no border)
        entry = tk.Entry(row, width=5, justify='center', bd=0, highlightthickness=0,
                        bg='#2d2d2d', fg='#e0e0e0', insertbackground='white')
        entry.pack(side='left')
        entry.insert(0, str(var.get()))

        def on_entry_change(event=None):
            try:
                val = int(entry.get())
                var.set(val)  # No clamping - accept any value
                self.save_settings()
            except ValueError:
                entry.delete(0, 'end')
                entry.insert(0, str(var.get()))

        def on_var_change(*args):
            entry.delete(0, 'end')
            entry.insert(0, str(var.get()))

        entry.bind('<Return>', on_entry_change)
        entry.bind('<FocusOut>', on_entry_change)
        var.trace_add('write', on_var_change)

        if unit:
            ttk.Label(row, text=unit).pack(side='left')

    def start_recording_mine(self):
        self._recording_previous_value = self.mine_hotkey_var.get()
        self.recording_mine = True
        self.recording_triggernade = False
        self.recording_espam = False
        self.recording_dc_both = False
        self.recording_dc_outbound = False
        self.recording_dc_inbound = False
        self.recording_tamper = False
        self.recording_minimize = False
        self.recording_tray = False
        self.mine_record_btn.config(text="...")
        self.mine_hotkey_var.set("Press key...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()

    def _show_direction_picker(self):
        """Show radial compass popup with hover detection using images"""
        import math
        from PIL import Image, ImageTk

        # Create dark overlay over app
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.configure(bg='black')
        overlay.attributes('-alpha', 0.7)  # Semi-transparent
        overlay.geometry(f"{self.root.winfo_width()}x{self.root.winfo_height()}+{self.root.winfo_x()}+{self.root.winfo_y()}")

        # Create popup for direction picker
        popup = tk.Toplevel(self.root)
        popup.title("Select Direction")
        popup.overrideredirect(True)
        popup.configure(bg='black')
        popup.attributes('-transparentcolor', 'black')  # Make black corners transparent
        popup.attributes('-topmost', True)

        # Load direction images (handle PyInstaller bundle)
        if getattr(sys, 'frozen', False):
            script_dir = sys._MEIPASS
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))

        img_files = {
            "NONE": "NONE.png", "N": "N.png", "NE": "NE.png",
            "E": "E.png", "SE": "SE.png", "S": "S.png", "SW": "SW.png"
        }
        images = {}
        scale = 1.1  # Scale up 10%
        for name, filename in img_files.items():
            path = os.path.join(script_dir, filename)
            if os.path.exists(path):
                img = Image.open(path)
                # Scale up by 10%
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                images[name] = ImageTk.PhotoImage(img)

        if not images or "NONE" not in images:
            popup.destroy()
            return

        # Get image size
        img_width = images["NONE"].width()
        img_height = images["NONE"].height()
        center_x = img_width // 2
        center_y = img_height // 2

        # Title label above canvas
        title_label = tk.Label(popup, text="Select Slot", bg='white', fg='black', font=('Arial', 12, 'bold'), padx=10, pady=5)
        title_label.pack(pady=(5, 10))

        # Create canvas
        canvas = tk.Canvas(popup, width=img_width, height=img_height, bg='black', highlightthickness=0)
        canvas.pack()
        canvas.create_image(0, 0, anchor='nw', image=images["NONE"], tags="radial")
        # White circle border (3px)
        canvas.create_oval(1, 1, img_width - 1, img_height - 1, outline='white', width=3, tags="border")
        # Show current selection in center (3px up from center)
        selected = self.mine_q_direction_var.get()
        canvas.create_text(center_x - 3, center_y - 3, text=selected, fill='black', font=('Arial', 10, 'bold'), tags="dirtext")

        # Store reference to prevent garbage collection
        popup.images = images
        current_dir = [None]

        def angle_to_direction(angle):
            """Convert angle (degrees, 0=right, counter-clockwise) to direction"""
            # Calibrated: N=67-113, NE=22-70, E=wraps 0, SE=290-338, S=247-295, SW=206-253
            # Ring: inner=92, outer=151
            angle = angle % 360
            if 68 <= angle < 113:       # N
                return "N"
            elif 22 <= angle < 68:      # NE
                return "NE"
            elif angle < 22 or angle >= 338:  # E (wraps around 0)
                return "E"
            elif 292 <= angle < 338:    # SE
                return "SE"
            elif 250 <= angle < 292:    # S
                return "S"
            elif 206 <= angle < 250:    # SW
                return "SW"
            # 113-206 is NW/W territory - not selectable
            return None

        def on_mouse_move(event):
            dx = event.x - center_x
            dy = center_y - event.y  # Flip Y for standard math coords
            dist = math.sqrt(dx*dx + dy*dy)

            # Only detect in the ring area (not too close to center, not outside)
            if dist < 101 or dist > 166:  # Scaled 10% (92*1.1, 151*1.1)
                new_dir = None
            else:
                angle = math.degrees(math.atan2(dy, dx))
                if angle < 0:
                    angle += 360
                new_dir = angle_to_direction(angle)

            if new_dir != current_dir[0]:
                current_dir[0] = new_dir
                img_key = new_dir if new_dir and new_dir in images else "NONE"
                canvas.delete("radial")
                canvas.create_image(0, 0, anchor='nw', image=images[img_key], tags="radial")
                # Redraw border on top
                canvas.delete("border")
                canvas.create_oval(1, 1, img_width - 1, img_height - 1, outline='white', width=3, tags="border")
                # Update center text
                canvas.delete("dirtext")
                display_text = new_dir if new_dir else self.mine_q_direction_var.get()
                canvas.create_text(center_x - 3, center_y - 3, text=display_text, fill='black', font=('Arial', 10, 'bold'), tags="dirtext")

        def close_picker():
            overlay.destroy()
            popup.destroy()

        def on_click(event):
            if current_dir[0]:
                self.mine_q_direction_var.set(current_dir[0])
                self.mine_q_dir_btn.config(text=current_dir[0])
                self.save_settings()
            close_picker()

        def on_leave(event):
            # Reset to NONE when mouse leaves canvas
            if current_dir[0] is not None:
                current_dir[0] = None
                canvas.delete("radial")
                canvas.create_image(0, 0, anchor='nw', image=images["NONE"], tags="radial")
                canvas.delete("border")
                canvas.create_oval(1, 1, img_width - 1, img_height - 1, outline='white', width=3, tags="border")
                canvas.delete("dirtext")
                canvas.create_text(center_x - 3, center_y - 3, text=self.mine_q_direction_var.get(), fill='black', font=('Arial', 10, 'bold'), tags="dirtext")

        canvas.bind('<Motion>', on_mouse_move)
        canvas.bind('<Leave>', on_leave)
        canvas.bind('<Button-1>', on_click)
        popup.bind('<Button-1>', on_click)  # Click anywhere on popup closes
        overlay.bind('<Button-1>', lambda e: close_picker())  # Click overlay closes
        popup.bind('<Escape>', lambda e: close_picker())

        # Position centered over app window
        popup.update_idletasks()
        app_x = self.root.winfo_x()
        app_y = self.root.winfo_y()
        app_w = self.root.winfo_width()
        app_h = self.root.winfo_height()
        x = app_x + (app_w - img_width) // 2
        y = app_y + (app_h - img_height) // 2 - 60  # Move up 60px
        popup.geometry(f"+{x}+{y}")
        popup.focus_set()

    def _play_mine_q_radial(self):
        """Play Q radial selection using compass direction"""
        # Direction to delta mapping (distance of 300 pixels)
        # W and NW not available in game
        dist = 300
        direction_deltas = {
            "N":  (0, -dist),
            "NE": (dist, -dist),
            "E":  (dist, 0),
            "SE": (dist, dist),
            "S":  (0, dist),
            "SW": (-dist, dist),
        }

        direction = self.mine_q_direction_var.get()
        dx, dy = direction_deltas.get(direction, (0, dist))  # Default to South

        print(f"[Q RADIAL] Direction: {direction}, delta: ({dx}, {dy})")

        # Press Q and wait for radial to open
        pynput_keyboard.press('q')
        time.sleep(0.3)

        # Move in steps for natural feel
        steps = 10
        for i in range(steps):
            pynput_mouse.move(dx // steps, dy // steps)
            time.sleep(0.015)

        time.sleep(0.1)
        pynput_keyboard.release('q')
        print(f"[Q RADIAL] Done - selected {direction}")

    def start_reconnect_recording(self):
        """Record all clicks and key presses with positions"""
        from pynput import mouse, keyboard as kb

        self.reconnect_record_btn.config(text="Press ENTER...")
        self.reconnect_status_var.set("Press ENTER to start recording")
        self.show_overlay("Press ENTER to START", force=True)

        self._reconnect_recording = []
        self._reconnect_recording_active = False
        self._keys_held = set()  # Track held keys to avoid repeat spam

        def on_click(x, y, button, pressed):
            if not self._reconnect_recording_active:
                return
            btn_name = str(button).replace('Button.', '')
            event = {'type': 'click', 'x': x, 'y': y, 'button': btn_name, 'down': pressed}
            self._reconnect_recording.append(event)
            action = "down" if pressed else "up"
            print(f"[RECONNECT REC] {btn_name} {action} at ({x}, {y})")

        def on_key_press(key):
            # ENTER toggles recording
            if key == kb.Key.enter:
                if not self._reconnect_recording_active:
                    self._reconnect_recording_active = True
                    self._keys_held.clear()
                    self.root.after(0, lambda: self.reconnect_record_btn.config(text="Recording..."))
                    self.root.after(0, lambda: self.reconnect_status_var.set("Recording... ENTER to stop"))
                    self.root.after(0, lambda: self.show_overlay("Recording... ENTER to stop", force=True))
                else:
                    mouse_listener.stop()
                    keyboard_listener.stop()
                    self._reconnect_recording_active = False
                    self._save_reconnect_recording()
                    return False
                return

            if not self._reconnect_recording_active:
                return

            # Get key name
            try:
                key_name = key.char if hasattr(key, 'char') and key.char else str(key).replace('Key.', '')
            except:
                key_name = str(key).replace('Key.', '')

            # Skip if key already held (avoid repeat spam)
            if key_name in self._keys_held:
                return
            self._keys_held.add(key_name)

            event = {'type': 'key', 'key': key_name, 'down': True}
            self._reconnect_recording.append(event)
            print(f"[RECONNECT REC] key {key_name} down")

        def on_key_release(key):
            if not self._reconnect_recording_active:
                return
            if key == kb.Key.enter:
                return  # Don't record ENTER release

            try:
                key_name = key.char if hasattr(key, 'char') and key.char else str(key).replace('Key.', '')
            except:
                key_name = str(key).replace('Key.', '')

            # Remove from held keys
            self._keys_held.discard(key_name)

            event = {'type': 'key', 'key': key_name, 'down': False}
            self._reconnect_recording.append(event)
            print(f"[RECONNECT REC] key {key_name} up")

        mouse_listener = mouse.Listener(on_click=on_click)
        keyboard_listener = kb.Listener(on_press=on_key_press, on_release=on_key_release)
        mouse_listener.start()
        keyboard_listener.start()

    def _save_reconnect_recording(self):
        """Save the reconnect recording to file"""
        import json

        if len(self._reconnect_recording) < 2:
            self.reconnect_status_var.set("Recording too short")
            self.reconnect_record_btn.config(text="Record")
            self.show_overlay("Recording cancelled - too short", force=True)
            return

        # Save to file
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reconnect_macro.json")
        with open(save_path, 'w') as f:
            json.dump(self._reconnect_recording, f, indent=2)

        num_events = len(self._reconnect_recording)
        self.reconnect_status_var.set(f"Recorded: {num_events} events")
        self.reconnect_record_btn.config(text="Record")
        self.show_overlay(f"Saved {num_events} events", force=True)
        print(f"[RECONNECT REC] Saved {num_events} events to {save_path}")

    def play_reconnect_macro(self):
        """Play back the recorded reconnect macro"""
        import json

        # Default reconnect macro
        default_recording = [
            {"type": "key", "key": "tab", "down": True},
            {"type": "key", "key": "tab", "down": False},
            {"type": "click", "x": 195, "y": 1266, "button": "left", "down": True},
            {"type": "click", "x": 195, "y": 1266, "button": "left", "down": False},
            {"type": "key", "key": "shift", "down": True},
            {"type": "click", "x": 411, "y": 660, "button": "left", "down": True},
            {"type": "click", "x": 412, "y": 660, "button": "left", "down": False},
            {"type": "key", "key": "shift", "down": False},
            {"type": "key", "key": "esc", "down": True},
            {"type": "key", "key": "esc", "down": False},
            {"type": "key", "key": "esc", "down": True},
            {"type": "key", "key": "esc", "down": False},
            {"type": "click", "x": 491, "y": 1304, "button": "left", "down": True},
            {"type": "click", "x": 491, "y": 1304, "button": "left", "down": False},
            {"type": "click", "x": 3168, "y": 69, "button": "left", "down": True},
            {"type": "click", "x": 3169, "y": 66, "button": "left", "down": False},
            {"type": "click", "x": 584, "y": 957, "button": "left", "down": True},
            {"type": "click", "x": 584, "y": 957, "button": "left", "down": False},
        ]

        # Try to load custom recording, fall back to default
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reconnect_macro.json")
        if os.path.exists(save_path):
            with open(save_path, 'r') as f:
                recording = json.load(f)
            if not recording:
                recording = default_recording
        else:
            recording = default_recording

        self.reconnect_play_btn.config(text="Playing...")
        self.reconnect_status_var.set("Playing macro...")

        def playback():
            from pynput.mouse import Button
            from pynput.keyboard import Key

            button_map = {
                'left': Button.left,
                'right': Button.right,
                'middle': Button.middle,
            }

            def smooth_move(target_x, target_y, steps=20):
                """Fast smooth mouse movement with random curve each time"""
                import random
                import math
                current = pynput_mouse.position
                start_x, start_y = current[0], current[1]

                # Random curve: perpendicular offset that varies each move
                dx = target_x - start_x
                dy = target_y - start_y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 1:
                    return

                # Perpendicular direction (normalized)
                perp_x = -dy / dist
                perp_y = dx / dist

                # Random curve magnitude: -15 to +15 pixels at peak, changes each time
                curve_amount = random.uniform(-15, 15)

                for i in range(1, steps + 1):
                    progress = i / steps
                    # Base position along the line
                    base_x = start_x + dx * progress
                    base_y = start_y + dy * progress

                    # Arc offset: sine curve peaks in middle
                    arc = math.sin(progress * math.pi) * curve_amount
                    arc_x = perp_x * arc
                    arc_y = perp_y * arc

                    # Small jitter on top
                    jitter_x = random.uniform(-2, 2)
                    jitter_y = random.uniform(-2, 2)

                    # Last step always hits exact target
                    if i == steps:
                        pynput_mouse.position = (target_x, target_y)
                    else:
                        pynput_mouse.position = (int(base_x + arc_x + jitter_x), int(base_y + arc_y + jitter_y))

                    time.sleep(0.003)  # 3ms per step = 60ms total

            for event in recording:
                if event['type'] == 'click':
                    x, y = event['x'], event['y']
                    button = button_map.get(event['button'], Button.left)
                    smooth_move(x, y)
                    time.sleep(0.05)  # 50ms after move
                    if event['down']:
                        pynput_mouse.press(button)
                        time.sleep(0.03)  # 30ms after press
                    else:
                        pynput_mouse.release(button)
                        time.sleep(0.15)  # 150ms after release - let game register
                    print(f"[RECONNECT PLAY] {event['button']} {'down' if event['down'] else 'up'} at ({x}, {y})")

                elif event['type'] == 'key':
                    key_name = event['key']
                    is_press = event['down']
                    # Handle special keys (shift, ctrl, etc.)
                    special_keys = {
                        'shift': Key.shift, 'shift_l': Key.shift_l, 'shift_r': Key.shift_r,
                        'ctrl': Key.ctrl, 'ctrl_l': Key.ctrl_l, 'ctrl_r': Key.ctrl_r,
                        'alt': Key.alt, 'alt_l': Key.alt_l, 'alt_r': Key.alt_r,
                        'space': Key.space, 'enter': Key.enter, 'tab': Key.tab,
                        'backspace': Key.backspace, 'delete': Key.delete,
                        'esc': Key.esc, 'escape': Key.esc,
                        'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right,
                        'home': Key.home, 'end': Key.end, 'page_up': Key.page_up, 'page_down': Key.page_down,
                        'caps_lock': Key.caps_lock, 'num_lock': Key.num_lock,
                    }
                    key_lower = key_name.lower()
                    if key_lower in special_keys:
                        key = special_keys[key_lower]
                        if is_press:
                            pynput_keyboard.press(key)
                            time.sleep(0.03)  # 30ms after press
                        else:
                            pynput_keyboard.release(key)
                            # Longer delay after certain key releases
                            if key_lower in ('tab', 'esc', 'escape'):
                                time.sleep(0.3)  # 300ms for menu transitions
                            elif key_lower in ('shift', 'shift_l', 'shift_r'):
                                time.sleep(0.4)  # 400ms after shift - item transfer needs time
                            else:
                                time.sleep(0.1)  # 100ms after other key releases
                    elif len(key_name) == 1:
                        if is_press:
                            pynput_keyboard.press(key_name)
                            time.sleep(0.03)
                        else:
                            pynput_keyboard.release(key_name)
                            time.sleep(0.1)
                    action = "down" if is_press else "up"
                    print(f"[RECONNECT PLAY] key {key_name} {action}")

            self.root.after(0, lambda: self.reconnect_play_btn.config(text="Play"))
            self.root.after(0, lambda: self.reconnect_status_var.set("Playback complete"))
            self.root.after(0, lambda: self.show_overlay("Macro complete", force=True))

        threading.Thread(target=playback, daemon=True).start()

    def start_mine_drag_recording(self):
        """Record mine drag path - drag item to ground"""
        from pynput import mouse

        self.mine_drag_btn.config(text="Recording...")
        self.show_overlay("DRAG item to ground", force=True)
        self._mine_drag_started = False
        self._mine_drag_start_time = None

        def on_click(x, y, button, pressed):
            if button != mouse.Button.left:
                return

            if pressed:
                self._mine_drag_start_temp = (x, y)
                self._mine_drag_start_time = time.time()
                self._mine_drag_started = True
                self.root.after(0, lambda: self.show_overlay("Now RELEASE...", force=True))
            elif self._mine_drag_started:
                # Validate drag: >20ms hold and >50px distance
                duration_ms = (time.time() - self._mine_drag_start_time) * 1000
                dx = x - self._mine_drag_start_temp[0]
                dy = y - self._mine_drag_start_temp[1]
                distance = (dx*dx + dy*dy) ** 0.5

                if duration_ms < 20 or distance < 50:
                    # Not a valid drag, reset
                    self._mine_drag_started = False
                    self.root.after(0, lambda: self.show_overlay("DRAG item to ground", force=True))
                    return

                self.mine_drag_start = self._mine_drag_start_temp
                self.mine_drag_end = (x, y)
                self.config["mine_drag_start"] = list(self.mine_drag_start)
                self.config["mine_drag_end"] = list(self.mine_drag_end)
                save_config(self.config)
                self.mine_drag_var.set(f"{self.mine_drag_start} → {self.mine_drag_end}")
                self.root.after(0, lambda: self.mine_drag_btn.config(text="Record"))
                self.root.after(0, lambda: self.show_overlay("Recorded!", force=True))
                print(f"[MINE] Drag: {self.mine_drag_start} → {self.mine_drag_end}")
                # Clean up ESC hook on successful recording
                if esc_hook_ref[0]:
                    try:
                        keyboard.unhook(esc_hook_ref[0])
                    except:
                        pass
                return False  # Stop listener

        listener_ref = [None]
        esc_hook_ref = [None]
        listener_ref[0] = mouse.Listener(on_click=on_click)
        listener_ref[0].start()

        # ESC to cancel and stop all macros
        def on_esc():
            self._mine_recording_cancelled = True
            if listener_ref[0]:
                listener_ref[0].stop()
            self.root.after(0, lambda: self.mine_drag_btn.config(text="Record"))
            self.root.after(0, lambda: self.show_overlay("Cancelled", force=True))
            self.stop_all_macros()
            if esc_hook_ref[0]:
                try:
                    keyboard.unhook(esc_hook_ref[0])
                except:
                    pass

        esc_hook_ref[0] = keyboard.on_press_key('esc', lambda e: on_esc(), suppress=False)

    def start_recording_espam(self):
        self._recording_previous_value = self.espam_hotkey_var.get()
        self.recording_espam = True
        self.recording_triggernade = False
        self.recording_mine = False
        self.recording_dc_both = False
        self.recording_dc_outbound = False
        self.recording_dc_inbound = False
        self.recording_tamper = False
        self.recording_minimize = False
        self.recording_tray = False
        self.espam_record_btn.config(text="...")
        self.espam_hotkey_var.set("Press key...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()

    def start_recording_triggernade(self):
        self._recording_previous_value = self.triggernade_hotkey_var.get()
        self.recording_triggernade = True
        self.recording_quickdrop = False
        self.recording_espam = False
        self.recording_mine = False
        self.recording_dc_both = False
        self.recording_dc_outbound = False
        self.recording_dc_inbound = False
        self.recording_tamper = False
        self.recording_minimize = False
        self.recording_tray = False
        self.triggernade_record_btn.config(text="...")
        self.triggernade_hotkey_var.set("Press key...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()

    def start_recording_quickdrop(self):
        self._recording_previous_value = self.quickdrop_hotkey_var.get()
        self.recording_quickdrop = True
        self.recording_triggernade = False
        self.recording_espam = False
        self.recording_mine = False
        self.recording_dc_both = False
        self.recording_dc_outbound = False
        self.recording_dc_inbound = False
        self.recording_tamper = False
        self.recording_minimize = False
        self.recording_tray = False
        self.quickdrop_record_btn.config(text="...")
        self.quickdrop_hotkey_var.set("Press key...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()

    def start_quickdrop_pos_recording(self):
        """Record quick drop positions - right-click starts, left-click captures drop position"""
        from pynput import mouse

        self.quickdrop_pos_btn.config(text="Right-click...")
        self.show_overlay("RIGHT-CLICK on item", force=True)
        self._quickdrop_rclick_pos = None

        def on_click(x, y, button, pressed):
            if not pressed:
                return  # Only care about press, not release

            if button == mouse.Button.right and self._quickdrop_rclick_pos is None:
                # First: right-click position
                self._quickdrop_rclick_pos = (x, y)
                self.root.after(0, lambda: self.quickdrop_pos_btn.config(text="Left-click..."))
                self.root.after(0, lambda: self.show_overlay("LEFT-CLICK 'Drop to Ground'", force=True))
                print(f"[QUICKDROP] Right-click at {x}, {y}")

            elif button == mouse.Button.left and self._quickdrop_rclick_pos is not None:
                # Second: left-click position (drop to ground)
                self.quickdrop_rclick_pos = self._quickdrop_rclick_pos
                self.quickdrop_lclick_pos = (x, y)
                self.config["quickdrop_rclick_pos"] = list(self.quickdrop_rclick_pos)
                self.config["quickdrop_lclick_pos"] = list(self.quickdrop_lclick_pos)
                save_config(self.config)
                self.quickdrop_pos_var.set(f"R:{list(self.quickdrop_rclick_pos)} L:{list(self.quickdrop_lclick_pos)}")
                self.root.after(0, lambda: self.quickdrop_pos_btn.config(text="Record Pos"))
                self.root.after(0, lambda: self.show_overlay("Recorded!", force=True))
                print(f"[QUICKDROP] Left-click at {x}, {y}")
                print(f"[QUICKDROP] Positions: R:{self.quickdrop_rclick_pos} L:{self.quickdrop_lclick_pos}")
                return False  # Stop listener

        listener = mouse.Listener(on_click=on_click)
        listener.start()

    def start_drag_recording(self):
        """Start recording drag coordinates - 10 sec countdown, then waits for mouse down/up"""
        if self.recording_drag:
            return  # Already recording

        self.recording_drag = True
        self.drag_record_btn.config(text="10...")
        self.drag_label_var.set("Get ready...")

        # Start countdown
        self._drag_countdown(10)

    def start_recording_reconnect_hotkey(self):
        """Start recording hotkey for reconnect macro"""
        self._recording_previous_value = self.reconnect_hotkey_var.get()
        self.recording_reconnect = True
        self.recording_triggernade = False
        self.recording_espam = False
        self.recording_mine = False
        self.recording_dc_both = False
        self.recording_dc_outbound = False
        self.recording_dc_inbound = False
        self.recording_tamper = False
        self.recording_minimize = False
        self.recording_tray = False
        self.recording_stop = False
        self.reconnect_hk_btn.config(text="...")
        self.reconnect_hotkey_var.set("Press key...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()

    def _drag_countdown(self, seconds_left):
        """Countdown before starting drag recording"""
        if not self.recording_drag:
            return  # Cancelled

        if seconds_left > 0:
            self.drag_record_btn.config(text=f"{seconds_left}...")
            self.show_overlay(f"Drag recording in {seconds_left}...", force=True)
            self.root.after(1000, lambda: self._drag_countdown(seconds_left - 1))
        else:
            # Countdown done - start listening
            self._start_drag_listener()

    def _start_drag_listener(self):
        """Actually start the mouse listener for drag recording"""
        from pynput import mouse

        self.drag_record_btn.config(text="DRAG NOW")
        self.drag_label_var.set("Click and drag item!")
        self.show_overlay("DRAG NOW!", force=True)

        drag_start_pos = [None, None]

        def on_click(x, y, button, pressed):
            if button != mouse.Button.left:
                return  # Only track left clicks

            if pressed:
                # Mouse down - record start position
                drag_start_pos[0] = x
                drag_start_pos[1] = y
                self.root.after(0, lambda: self.drag_label_var.set(f"Start: ({x},{y}) - Release..."))
                self.root.after(0, lambda: self.show_overlay(f"Start: ({x},{y}) - Release...", force=True))
            else:
                # Mouse up - record end position and stop
                if drag_start_pos[0] is not None:
                    self.drag_start = (drag_start_pos[0], drag_start_pos[1])
                    self.drag_end = (x, y)

                    # Update UI
                    self.root.after(0, lambda: self.drag_label_var.set(
                        f"({self.drag_start[0]},{self.drag_start[1]}) → ({self.drag_end[0]},{self.drag_end[1]})"
                    ))
                    self.root.after(0, lambda: self.drag_record_btn.config(text="Record Drag"))

                    # Save to config
                    self.config["drag_start"] = list(self.drag_start)
                    self.config["drag_end"] = list(self.drag_end)
                    save_config(self.config)

                    print(f"[DRAG] Recorded: {self.drag_start} → {self.drag_end}")
                    self.root.after(0, lambda: self.show_overlay(f"Drag saved!", force=True))

                    self.recording_drag = False
                    return False  # Stop listener

        # Start mouse listener
        self.drag_mouse_listener = mouse.Listener(on_click=on_click)
        self.drag_mouse_listener.start()

    def _start_drag_position_listener(self, target='triggernade'):
        """Listen for drag and record start/end positions only"""
        from pynput import mouse

        if self._drag_recording_cancelled:
            return

        self.show_overlay("Click & drag NOW!", force=True)

        state = {'start_pos': None}
        listener_ref = [None]
        esc_hook_ref = [None]

        def on_click(x, y, button, pressed):
            if self._drag_recording_cancelled:
                return False  # Stop listener

            if button != mouse.Button.left:
                return

            # Convert to int (pynput can return floats on some systems)
            x, y = int(x), int(y)

            if pressed:
                state['start_pos'] = (x, y)
                self.show_overlay(f"Dragging from ({x},{y})...", force=True)
            else:
                if state['start_pos']:
                    start = state['start_pos']
                    end = (x, y)

                    self.trig_drag_start = start
                    self.trig_drag_end = end
                    self.config["trig_drag_start"] = list(start)
                    self.config["trig_drag_end"] = list(end)
                    self.trig_drag_var.set(f"({start[0]},{start[1]}) → ({end[0]},{end[1]})")
                    print(f"[TRIG DRAG] Recorded: {start} → {end}")

                    save_config(self.config)
                    self.show_overlay(f"Saved! {start} → {end}", force=True)
                    # Clean up ESC hook on successful recording
                    if esc_hook_ref[0]:
                        try:
                            keyboard.unhook(esc_hook_ref[0])
                        except:
                            pass
                    return False  # Stop listener

        listener_ref[0] = mouse.Listener(on_click=on_click)
        listener_ref[0].start()

        # ESC to cancel and stop all macros
        def on_esc():
            self._drag_recording_cancelled = True
            if listener_ref[0]:
                listener_ref[0].stop()
            self.root.after(0, lambda: self.show_overlay("Cancelled", force=True))
            self.stop_all_macros()
            if esc_hook_ref[0]:
                try:
                    keyboard.unhook(esc_hook_ref[0])
                except:
                    pass

        esc_hook_ref[0] = keyboard.on_press_key('esc', lambda e: on_esc(), suppress=False)

    def start_trig_drag_recording(self):
        """Record triggernade drag path - drag item to ground"""
        from pynput import mouse

        self.trig_drag_btn.config(text="Recording...")
        self.show_overlay("DRAG item to ground", force=True)
        self._trig_drag_started = False
        self._trig_drag_start_time = None

        def on_click(x, y, button, pressed):
            if button != mouse.Button.left:
                return

            if pressed:
                self._trig_drag_start_temp = (x, y)
                self._trig_drag_start_time = time.time()
                self._trig_drag_started = True
                self.root.after(0, lambda: self.show_overlay("Now RELEASE...", force=True))
            elif self._trig_drag_started:
                # Validate drag: >20ms hold and >50px distance
                duration_ms = (time.time() - self._trig_drag_start_time) * 1000
                dx = x - self._trig_drag_start_temp[0]
                dy = y - self._trig_drag_start_temp[1]
                distance = (dx*dx + dy*dy) ** 0.5

                if duration_ms < 20 or distance < 50:
                    # Not a valid drag, reset
                    self._trig_drag_started = False
                    self.root.after(0, lambda: self.show_overlay("DRAG item to ground", force=True))
                    return

                self.trig_drag_start = self._trig_drag_start_temp
                self.trig_drag_end = (x, y)
                self.config["trig_drag_start"] = list(self.trig_drag_start)
                self.config["trig_drag_end"] = list(self.trig_drag_end)
                save_config(self.config)
                self.trig_drag_var.set(f"{self.trig_drag_start} → {self.trig_drag_end}")
                self.root.after(0, lambda: self.trig_drag_btn.config(text="Record"))
                self.root.after(0, lambda: self.show_overlay("Recorded!", force=True))
                print(f"[TRIG] Drag: {self.trig_drag_start} → {self.trig_drag_end}")
                # Clean up ESC hook on successful recording
                if esc_hook_ref[0]:
                    try:
                        keyboard.unhook(esc_hook_ref[0])
                    except:
                        pass
                return False  # Stop listener

        listener_ref = [None]
        esc_hook_ref = [None]
        listener_ref[0] = mouse.Listener(on_click=on_click)
        listener_ref[0].start()

        # ESC to cancel and stop all macros
        def on_esc():
            self._drag_recording_cancelled = True
            if listener_ref[0]:
                listener_ref[0].stop()
            self.root.after(0, lambda: self.trig_drag_btn.config(text="Record"))
            self.root.after(0, lambda: self.show_overlay("Cancelled", force=True))
            self.stop_all_macros()
            if esc_hook_ref[0]:
                try:
                    keyboard.unhook(esc_hook_ref[0])
                except:
                    pass

        esc_hook_ref[0] = keyboard.on_press_key('esc', lambda e: on_esc(), suppress=False)

    def _drag_countdown(self, seconds_left, target, record_drag=True):
        if self._drag_recording_cancelled:
            return  # Cancelled
        if seconds_left > 0:
            self.show_overlay(f"Get ready... {seconds_left}", force=True)
            self.root.after(1000, lambda: self._drag_countdown(seconds_left - 1, target, record_drag))
        else:
            if record_drag:
                self._start_drag_position_listener(target)
            else:
                self._start_position_listener(target)

    def _start_position_listener(self, target):
        """Listen for single click to record position"""
        from pynput import mouse

        if self._drag_recording_cancelled:
            return

        self.show_overlay("Click position NOW!", force=True)

        listener_ref = [None]
        esc_hook_ref = [None]

        def on_click(x, y, button, pressed):
            if self._drag_recording_cancelled:
                return False  # Stop listener

            if button != mouse.Button.left:
                return
            if not pressed:  # On release
                x, y = int(x), int(y)
                pos = (x, y)

                self.trig_slot_pos = pos
                self.config["trig_slot_pos"] = list(pos)
                self.trig_drag_var.set(f"Pos: ({x}, {y})")
                print(f"[TRIG POS] Recorded: {pos}")

                save_config(self.config)
                print(f"[CONFIG] Saved to: {CONFIG_FILE}")
                self.show_overlay(f"Position saved: ({x}, {y})", force=True)
                # Clean up ESC hook on successful recording
                if esc_hook_ref[0]:
                    try:
                        keyboard.unhook(esc_hook_ref[0])
                    except:
                        pass
                return False  # Stop listener

        listener_ref[0] = mouse.Listener(on_click=on_click)
        listener_ref[0].start()

        # ESC to cancel and stop all macros
        def on_esc():
            self._drag_recording_cancelled = True
            if listener_ref[0]:
                listener_ref[0].stop()
            self.root.after(0, lambda: self.show_overlay("Cancelled", force=True))
            self.stop_all_macros()
            if esc_hook_ref[0]:
                try:
                    keyboard.unhook(esc_hook_ref[0])
                except:
                    pass

        esc_hook_ref[0] = keyboard.on_press_key('esc', lambda e: on_esc(), suppress=False)

    def start_slot_recording(self):
        """Record drop position - click where the item slot is"""
        self.slot_record_btn.config(text="3...")
        self._slot_countdown(3)

    def _slot_countdown(self, seconds_left):
        if seconds_left > 0:
            self.slot_record_btn.config(text=f"{seconds_left}...")
            self.show_overlay(f"Click slot in {seconds_left}...", force=True)
            self.root.after(1000, lambda: self._slot_countdown(seconds_left - 1))
        else:
            self._start_slot_listener()

    def _start_slot_listener(self):
        """Listen for click to record drop position"""
        from pynput import mouse

        self.slot_record_btn.config(text="CLICK!")
        self.show_overlay("CLICK ON SLOT!", force=True)

        def on_click(x, y, button, pressed):
            if button == mouse.Button.left and pressed:
                self.drag_start = (x, y)

                # Save to config
                self.config["drop_position"] = [x, y]
                save_config(self.config)

                self.root.after(0, lambda: self.slot_pos_var.set(f"({x}, {y})"))
                self.root.after(0, lambda: self.slot_record_btn.config(text="Record"))
                self.root.after(0, lambda: self.show_overlay(f"Position: ({x}, {y})", force=True))
                print(f"[SLOT] Recorded drop position: ({x}, {y})")
                return False  # Stop listener

        listener = mouse.Listener(on_click=on_click)
        listener.start()

    def start_recording_stop(self):
        """Start recording hotkey for Stop All"""
        print("[DEBUG] start_recording_stop() called")
        self._recording_previous_value = self.stop_hotkey_var.get()
        self.recording_stop = True
        self.recording_triggernade = False
        self.recording_espam = False
        self.recording_mine = False
        self.recording_dc_both = False
        self.recording_dc_outbound = False
        self.recording_dc_inbound = False
        self.recording_tamper = False
        self.recording_minimize = False
        self.recording_tray = False
        self.stop_record_btn.config(text="...")
        self.stop_hotkey_var.set("Press key...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()
        print(f"[DEBUG] recording_stop={self.recording_stop}, bound KeyPress, focus forced")

    def on_key_press(self, event):
        print(f"[DEBUG] on_key_press called: key={event.keysym}, recording_stop={self.recording_stop}")
        if not self.recording_triggernade and not self.recording_quickdrop and not self.recording_mine and not self.recording_espam and not self.recording_dc_both and not self.recording_dc_outbound and not self.recording_dc_inbound and not self.recording_tamper and not self.recording_minimize and not self.recording_tray and not self.recording_stop and not getattr(self, 'recording_reconnect', False):
            print("[DEBUG] on_key_press: early return - no recording flags set")
            return

        # Use keyboard library to check modifiers (tkinter state flags are unreliable)
        parts = []
        if keyboard.is_pressed('ctrl'):
            parts.append("ctrl")
        if keyboard.is_pressed('alt'):
            parts.append("alt")
        if keyboard.is_pressed('shift'):
            parts.append("shift")

        # Map tkinter keysyms to keyboard library key names
        tkinter_to_keyboard = {
            'next': 'page down',
            'prior': 'page up',
            'escape': 'esc',
            'return': 'enter',
            'control_l': 'ctrl',
            'control_r': 'ctrl',
            'alt_l': 'alt',
            'alt_r': 'alt',
            'shift_l': 'shift',
            'shift_r': 'shift',
            'caps_lock': 'caps lock',
            'num_lock': 'num lock',
            'scroll_lock': 'scroll lock',
            'print': 'print screen',
            'insert': 'insert',
            'delete': 'delete',
            'home': 'home',
            'end': 'end',
            'up': 'up',
            'down': 'down',
            'left': 'left',
            'right': 'right',
            'space': 'space',
            'tab': 'tab',
            'backspace': 'backspace',
            # Symbol keys
            'minus': '-',
            'plus': '+',
            'equal': '=',
            'bracketleft': '[',
            'bracketright': ']',
            'semicolon': ';',
            'apostrophe': "'",
            'grave': '`',
            'backslash': '\\',
            'comma': ',',
            'period': '.',
            'slash': '/',
            # Numpad
            'kp_subtract': '-',
            'kp_add': '+',
            'kp_multiply': '*',
            'kp_divide': '/',
            'kp_decimal': '.',
            'kp_enter': 'enter',
        }

        key = event.keysym.lower()
        key = tkinter_to_keyboard.get(key, key)  # Map if exists, otherwise use as-is

        # ESC clears the hotkey
        if key == 'esc':
            if self.recording_triggernade:
                self.triggernade_hotkey_var.set("")
                self.triggernade_record_btn.config(text="Set")
                self.recording_triggernade = False
            elif self.recording_quickdrop:
                self.quickdrop_hotkey_var.set("")
                self.quickdrop_record_btn.config(text="Set")
                self.recording_quickdrop = False
            elif self.recording_mine:
                self.mine_hotkey_var.set("")
                self.mine_record_btn.config(text="Set")
                self.recording_mine = False
            elif self.recording_espam:
                self.espam_hotkey_var.set("")
                self.espam_record_btn.config(text="Set")
                self.recording_espam = False
            elif self.recording_stop:
                self.stop_hotkey_var.set("")
                self.stop_record_btn.config(text="Set")
                self.recording_stop = False
            elif self.recording_dc_both:
                self.dc_both_hotkey_var.set("")
                self.dc_both_record_btn.config(text="Set")
                self.recording_dc_both = False
            elif self.recording_dc_outbound:
                self.dc_outbound_hotkey_var.set("")
                self.dc_outbound_record_btn.config(text="Set")
                self.recording_dc_outbound = False
            elif self.recording_dc_inbound:
                self.dc_inbound_hotkey_var.set("")
                self.dc_inbound_record_btn.config(text="Set")
                self.recording_dc_inbound = False
            elif self.recording_tamper:
                self.tamper_hotkey_var.set("")
                self.tamper_record_btn.config(text="Set")
                self.recording_tamper = False
            elif self.recording_minimize:
                self.minimize_hotkey_var.set("")
                self.minimize_record_btn.config(text="Set")
                self.recording_minimize = False
            elif self.recording_tray:
                self.tray_hotkey_var.set("")
                self.tray_record_btn.config(text="Set")
                self.recording_tray = False
            elif getattr(self, 'recording_reconnect', False):
                self.reconnect_hotkey_var.set("")
                self.reconnect_hk_btn.config(text="Set")
                self.recording_reconnect = False
            self.root.unbind("<KeyPress>")
            self.root.update_idletasks()  # Force GUI refresh
            self.save_settings()
            self.register_hotkeys()
            return

        modifier_keys = ['ctrl', 'alt', 'shift', 'control_l', 'control_r', 'alt_l', 'alt_r', 'shift_l', 'shift_r', 'meta_l', 'meta_r']
        if key not in modifier_keys:
            parts.append(key)
            hotkey = "+".join(parts)

            # Clear this hotkey from any other action first
            all_hotkey_vars = [
                self.triggernade_hotkey_var,
                self.quickdrop_hotkey_var,
                self.mine_hotkey_var,
                self.espam_hotkey_var,
                self.stop_hotkey_var,
                self.dc_both_hotkey_var,
                self.dc_outbound_hotkey_var,
                self.dc_inbound_hotkey_var,
                self.tamper_hotkey_var,
                self.minimize_hotkey_var,
                self.tray_hotkey_var,
                self.reconnect_hotkey_var,
            ]
            for var in all_hotkey_vars:
                if var.get() == hotkey:
                    var.set("")

            if self.recording_triggernade:
                self.triggernade_hotkey_var.set(hotkey)
                self.triggernade_record_btn.config(text="Set")
                self.recording_triggernade = False
            elif self.recording_quickdrop:
                self.quickdrop_hotkey_var.set(hotkey)
                self.quickdrop_record_btn.config(text="Set")
                self.recording_quickdrop = False
            elif self.recording_mine:
                self.mine_hotkey_var.set(hotkey)
                self.mine_record_btn.config(text="Set")
                self.recording_mine = False
            elif self.recording_espam:
                self.espam_hotkey_var.set(hotkey)
                self.espam_record_btn.config(text="Set")
                self.recording_espam = False
            elif self.recording_stop:
                self.stop_hotkey_var.set(hotkey)
                self.stop_record_btn.config(text="Set")
                self.recording_stop = False
            elif self.recording_dc_both:
                self.dc_both_hotkey_var.set(hotkey)
                self.dc_both_record_btn.config(text="Set")
                self.recording_dc_both = False
            elif self.recording_dc_outbound:
                self.dc_outbound_hotkey_var.set(hotkey)
                self.dc_outbound_record_btn.config(text="Set")
                self.recording_dc_outbound = False
            elif self.recording_dc_inbound:
                self.dc_inbound_hotkey_var.set(hotkey)
                self.dc_inbound_record_btn.config(text="Set")
                self.recording_dc_inbound = False
            elif self.recording_tamper:
                self.tamper_hotkey_var.set(hotkey)
                self.tamper_record_btn.config(text="Set")
                self.recording_tamper = False
            elif self.recording_minimize:
                self.minimize_hotkey_var.set(hotkey)
                self.minimize_record_btn.config(text="Set")
                self.recording_minimize = False
            elif self.recording_tray:
                self.tray_hotkey_var.set(hotkey)
                self.tray_record_btn.config(text="Set")
                self.recording_tray = False
            elif getattr(self, 'recording_reconnect', False):
                self.reconnect_hotkey_var.set(hotkey)
                self.reconnect_hk_btn.config(text="Set")
                self.recording_reconnect = False
            self.root.unbind("<KeyPress>")
            self.root.update_idletasks()  # Force GUI refresh
            self.save_settings()
            self.register_hotkeys()

    def toggle_stay_on_top(self):
        """Toggle window always-on-top setting"""
        stay_on_top = self.stay_on_top_var.get()
        self.root.attributes('-topmost', stay_on_top)
        self.save_settings()
        print(f"[UI] Stay on top: {stay_on_top}")

    def _reset_dc_buttons(self):
        """Reset all DC buttons to default state"""
        self.dc_both_btn.config(text="DC BOTH", bg='#3c3c3c')
        self.dc_outbound_btn.config(text="DC OUTBOUND", bg='#3c3c3c')
        self.dc_inbound_btn.config(text="DC INBOUND", bg='#3c3c3c')

    def toggle_dc_both(self):
        """Toggle disconnect both inbound + outbound"""
        if is_dropping():
            # Reconnect
            stop_packet_drop()
            self._reset_dc_buttons()
            self.root.after(0, lambda: self.show_overlay("RECONNECTED"))
        else:
            start_packet_drop(outbound=True, inbound=True)
            self._reset_dc_buttons()
            self.dc_both_btn.config(text="RECONNECT", bg='#e94560')
            self.root.after(0, lambda: self.show_overlay("DC BOTH"))

    def toggle_dc_outbound(self):
        """Toggle disconnect outbound only"""
        if is_dropping():
            # Reconnect
            stop_packet_drop()
            self._reset_dc_buttons()
            self.root.after(0, lambda: self.show_overlay("RECONNECTED"))
        else:
            start_packet_drop(outbound=True, inbound=False)
            self._reset_dc_buttons()
            self.dc_outbound_btn.config(text="RECONNECT", bg='#e94560')
            self.root.after(0, lambda: self.show_overlay("DC OUTBOUND"))

    def toggle_dc_inbound(self):
        """Toggle disconnect inbound only"""
        if is_dropping():
            # Reconnect
            stop_packet_drop()
            self._reset_dc_buttons()
            self.root.after(0, lambda: self.show_overlay("RECONNECTED"))
        else:
            start_packet_drop(outbound=False, inbound=True)
            self._reset_dc_buttons()
            self.dc_inbound_btn.config(text="RECONNECT", bg='#e94560')
            self.root.after(0, lambda: self.show_overlay("DC INBOUND"))

    def toggle_tamper(self):
        """Toggle packet tampering - corrupts packets but still sends them"""
        if self.tampering:
            stop_packet_tamper()
            self.tamper_btn.config(text="TAMPER", bg='#3c3c3c')
            self.tampering = False
            self.root.after(0, lambda: self.show_overlay("TAMPER OFF"))
        else:
            start_packet_tamper(outbound=True, inbound=True)
            self.tamper_btn.config(text="STOP TAMPER", bg='#ff8c00')
            self.tampering = True
            self.root.after(0, lambda: self.show_overlay("TAMPER ON"))

    def start_recording_dc_both(self):
        """Start recording hotkey for DC both"""
        self._recording_previous_value = self.dc_both_hotkey_var.get()
        self.recording_dc_both = True
        self.recording_dc_outbound = False
        self.recording_dc_inbound = False
        self.recording_tamper = False
        self.recording_triggernade = False
        self.recording_espam = False
        self.recording_mine = False
        self.recording_minimize = False
        self.recording_tray = False
        self.dc_both_record_btn.config(text="...")
        self.dc_both_hotkey_var.set("...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()

    def start_recording_dc_outbound(self):
        """Start recording hotkey for DC outbound"""
        self._recording_previous_value = self.dc_outbound_hotkey_var.get()
        self.recording_dc_outbound = True
        self.recording_dc_both = False
        self.recording_dc_inbound = False
        self.recording_tamper = False
        self.recording_triggernade = False
        self.recording_espam = False
        self.recording_mine = False
        self.recording_minimize = False
        self.recording_tray = False
        self.dc_outbound_record_btn.config(text="...")
        self.dc_outbound_hotkey_var.set("...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()

    def start_recording_dc_inbound(self):
        """Start recording hotkey for DC inbound"""
        self._recording_previous_value = self.dc_inbound_hotkey_var.get()
        self.recording_dc_inbound = True
        self.recording_dc_both = False
        self.recording_dc_outbound = False
        self.recording_tamper = False
        self.recording_triggernade = False
        self.recording_espam = False
        self.recording_mine = False
        self.recording_minimize = False
        self.recording_tray = False
        self.dc_inbound_record_btn.config(text="...")
        self.dc_inbound_hotkey_var.set("...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()

    def start_recording_tamper(self):
        """Start recording hotkey for Tamper"""
        self._recording_previous_value = self.tamper_hotkey_var.get()
        self.recording_tamper = True
        self.recording_dc_both = False
        self.recording_dc_outbound = False
        self.recording_dc_inbound = False
        self.recording_triggernade = False
        self.recording_espam = False
        self.recording_mine = False
        self.recording_minimize = False
        self.recording_tray = False
        self.tamper_record_btn.config(text="...")
        self.tamper_hotkey_var.set("...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()

    def start_recording_minimize(self):
        """Start recording hotkey for minimize window"""
        self._recording_previous_value = self.minimize_hotkey_var.get()
        self.recording_minimize = True
        self.recording_tray = False
        self.recording_triggernade = False
        self.recording_espam = False
        self.recording_dc_both = False
        self.recording_dc_outbound = False
        self.recording_dc_inbound = False
        self.recording_tamper = False
        self.recording_mine = False
        self.minimize_record_btn.config(text="...")
        self.minimize_hotkey_var.set("Press key...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()

    def start_recording_tray(self):
        """Start recording hotkey for minimize to tray"""
        self._recording_previous_value = self.tray_hotkey_var.get()
        self.recording_tray = True
        self.recording_minimize = False
        self.recording_triggernade = False
        self.recording_espam = False
        self.recording_dc_both = False
        self.recording_dc_outbound = False
        self.recording_dc_inbound = False
        self.recording_tamper = False
        self.recording_mine = False
        self.tray_record_btn.config(text="...")
        self.tray_hotkey_var.set("Press key...")
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_force()

    def save_settings(self):
        # Triggernade settings
        self.config["triggernade_hotkey"] = self.triggernade_hotkey_var.get()
        self.config["triggernade_repeat"] = self.triggernade_repeat_var.get()
        self.config["triggernade_q_spam"] = self.triggernade_q_spam_var.get()
        # Quick Drop settings
        self.config["quickdrop_hotkey"] = self.quickdrop_hotkey_var.get()
        self.config["quickdrop_repeat"] = self.quickdrop_repeat_var.get()
        self.config["quickdrop_rclick_pos"] = list(self.quickdrop_rclick_pos)
        self.config["quickdrop_lclick_pos"] = list(self.quickdrop_lclick_pos)
        self.config["espam_hotkey"] = self.espam_hotkey_var.get()
        self.config["wait_before_espam"] = self.wait_before_espam_var.get()
        self.config["espam_duration"] = self.espam_duration_var.get()
        self.config["wait_before_cycle"] = self.wait_before_cycle_var.get()
        self.config["trig_dc_throws"] = self.trig_dc_throws_var.get()
        self.config["trig_throw_delay"] = self.trig_throw_delay_var.get()
        self.config["trig_reconnect_after"] = self.trig_reconnect_after_var.get()
        self.config["trig_m1_hold"] = self.trig_m1_hold_var.get()
        self.config["trig_m2_hold"] = self.trig_m2_hold_var.get()
        self.config["trig_dc_delay"] = self.trig_dc_delay_var.get()
        # Wolfpack loop settings
        self.config["wolfpack_m1_hold"] = self.wolfpack_m1_hold_var.get()
        self.config["wolfpack_m1_gap"] = self.wolfpack_m1_gap_var.get()
        self.config["wolfpack_dc_hold"] = self.wolfpack_dc_hold_var.get()
        self.config["wolfpack_dc_gap"] = self.wolfpack_dc_gap_var.get()
        # Mine settings
        self.config["mine_hotkey"] = self.mine_hotkey_var.get()
        self.config["mine_repeat"] = self.mine_repeat_var.get()
        self.config["mine_cook"] = self.mine_cook_var.get()
        self.config["mine_dc_delay"] = self.mine_dc_delay_var.get()
        self.config["mine_click_delay"] = self.mine_click_delay_var.get()
        self.config["mine_pickup_hold"] = self.mine_pickup_hold_var.get()
        self.config["mine_e_delay"] = self.mine_e_delay_var.get()
        self.config["mine_loop_delay"] = self.mine_loop_delay_var.get()
        self.config["mine_reselect"] = self.mine_reselect_var.get()
        self.config["mine_q_mode"] = self.mine_q_mode_var.get()
        self.config["mine_q_direction"] = self.mine_q_direction_var.get()
        self.config["mine_nudge"] = self.mine_nudge_var.get()
        self.config["mine_nudge_px"] = self.mine_nudge_px_var.get()
        # E-spam settings
        self.config["espam_hold_mode"] = self.espam_hold_mode_var.get()
        self.config["espam_repeat_delay"] = self.espam_repeat_delay_var.get()
        # Quick disconnect hotkeys
        self.config["dc_both_hotkey"] = self.dc_both_hotkey_var.get()
        self.config["dc_outbound_hotkey"] = self.dc_outbound_hotkey_var.get()
        self.config["dc_inbound_hotkey"] = self.dc_inbound_hotkey_var.get()
        self.config["tamper_hotkey"] = self.tamper_hotkey_var.get()
        # General settings
        self.config["stay_on_top"] = self.stay_on_top_var.get()
        self.config["show_overlay"] = self.show_overlay_var.get()
        self.config["timing_variance"] = self.timing_variance_var.get()
        # Window hotkeys
        self.config["minimize_hotkey"] = self.minimize_hotkey_var.get()
        self.config["tray_hotkey"] = self.tray_hotkey_var.get()
        # Reconnect macro hotkey
        self.config["reconnect_hotkey"] = self.reconnect_hotkey_var.get()
        # Stop all hotkey
        self.config["stop_hotkey"] = self.stop_hotkey_var.get()
        save_config(self.config)

    def reset_triggernade_defaults(self):
        """Reset all triggernade timing parameters to defaults (from working recording)"""
        self.wait_before_espam_var.set(0)  # E spam starts during M1 spam (interleaved)
        self.espam_duration_var.set(250)  # E spam duration
        self.wait_before_cycle_var.set(100)
        self.trig_dc_throws_var.set(10)  # 10 M1s after reconnect
        self.trig_throw_delay_var.set(100)  # ~100ms between M1s
        self.trig_reconnect_after_var.set(1)  # Reconnect after first M1
        self.trig_m1_hold_var.set(65)  # Hold M1 65ms before M2
        self.trig_m2_hold_var.set(51)  # Hold M2 for 51ms
        self.trig_drag_speed_var.set(8)  # Drag speed
        self.trig_dc_delay_var.set(10)  # Delay before DC
        self.trig_m1_before_interweave_var.set(1)  # 1 M1 before E interweave
        self.triggernade_q_spam_var.set(False)  # Q spam disabled by default
        # Wolfpack loop settings
        self.wolfpack_m1_hold_var.set(20)
        self.wolfpack_m1_gap_var.set(20)
        self.wolfpack_dc_hold_var.set(20)
        self.wolfpack_dc_gap_var.set(600)
        # Note: Positions are NOT reset - only timing parameters
        self.save_settings()
        print("[RESET] Triggernade parameters reset to defaults (positions preserved)")

    def reset_mine_defaults(self):
        """Reset all mine dupe timing parameters to defaults (based on your successful recordings)"""
        # These are from your exact timings that worked 100%
        self.mine_cook_var.set(236)  # Cook time (M1 to TAB)
        self.mine_dc_delay_var.set(99)  # TAB to DC delay
        self.mine_drag_speed_var.set(8)  # Drag speed
        self.mine_pre_close_var.set(100)  # After drag to TAB close
        self.mine_tab_hold_var.set(80)  # TAB hold duration
        self.mine_close_reconnect_var.set(409)  # TAB close to reconnect
        self.mine_click_delay_var.set(7)  # Reconnect to pickup click (INSTANT!)
        self.mine_pickup_hold_var.set(1336)  # Pickup click hold
        self.mine_e_delay_var.set(868)  # After pickup to E
        self.mine_loop_delay_var.set(550)  # Loop delay
        self.mine_reselect_var.set(True)
        self.mine_nudge_var.set(True)
        self.mine_nudge_px_var.set(50)
        # Q radial mode with default direction
        self.mine_q_mode_var.set("radial")
        self.mine_q_direction_var.set("S")
        self.mine_q_dir_btn.config(text="S")
        # Default positions (for 4K resolution)
        self.mine_drag_start = (3032, 1236)
        self.mine_drag_end = (3171, 1593)
        self.mine_drag_var.set(f"{self.mine_drag_start} → {self.mine_drag_end}")
        self.save_settings()
        print("[RESET] Mine dupe parameters reset to YOUR successful timings")

    def reset_all_settings(self):
        """Reset ALL settings including hotkeys and recordings to factory defaults"""
        import tkinter.messagebox as mb
        if not mb.askyesno("Reset All Settings", "This will reset EVERYTHING including:\n\n• All hotkeys\n• All timing settings\n• All recorded positions\n• Drag drop preference\n\nAre you sure?"):
            return

        # Clear config file completely
        self.config = {}
        save_config(self.config)

        # Reset ALL hotkeys
        print("[RESET] Clearing all hotkeys...")
        self.triggernade_hotkey_var.set("")
        self.espam_hotkey_var.set("")
        self.dc_both_hotkey_var.set("")
        self.dc_outbound_hotkey_var.set("")
        self.dc_inbound_hotkey_var.set("")
        self.tamper_hotkey_var.set("")
        self.mine_hotkey_var.set("")
        self.stop_hotkey_var.set("esc")  # Default is esc
        self.minimize_hotkey_var.set("")
        self.tray_hotkey_var.set("")
        print("[RESET] All hotkeys cleared")

        # Reset checkboxes
        print("[RESET] Resetting checkboxes...")
        self.show_overlay_var.set(True)
        self.stay_on_top_var.set(False)
        self.triggernade_repeat_var.set(True)

        # Reset ALL timing sliders and positions
        print("[RESET] Resetting all timing defaults...")
        self.reset_triggernade_defaults()
        self.reset_mine_defaults()

        # Re-register hotkeys (will be empty now)
        self.register_hotkeys()

        print("[RESET] ALL settings reset to factory defaults")
        self.show_overlay("All settings reset!")

    # ===== EXPORT/IMPORT SETTINGS =====
    def _get_triggernade_settings(self):
        """Get all triggernade-related settings as a dict"""
        return {
            "triggernade_hotkey": self.triggernade_hotkey_var.get(),
            "triggernade_repeat": self.triggernade_repeat_var.get(),
            "triggernade_q_spam": self.triggernade_q_spam_var.get(),
            "trig_m1_hold": self.trig_m1_hold_var.get(),
            "trig_m2_hold": self.trig_m2_hold_var.get(),
            "trig_drag_speed": self.trig_drag_speed_var.get(),
            "trig_dc_delay": self.trig_dc_delay_var.get(),
            "trig_dc_throws": self.trig_dc_throws_var.get(),
            "trig_throw_delay": self.trig_throw_delay_var.get(),
            "trig_reconnect_after": self.trig_reconnect_after_var.get(),
            "wait_before_espam": self.wait_before_espam_var.get(),
            "espam_duration": self.espam_duration_var.get(),
            "trig_m1_before_interweave": self.trig_m1_before_interweave_var.get(),
            "wait_before_cycle": self.wait_before_cycle_var.get(),
            "trig_slot_pos": list(self.trig_slot_pos) if self.trig_slot_pos else None,
            "trig_drop_pos": list(self.trig_drop_pos) if self.trig_drop_pos else None,
            "wolfpack_m1_hold": self.wolfpack_m1_hold_var.get(),
            "wolfpack_m1_gap": self.wolfpack_m1_gap_var.get(),
            "wolfpack_dc_hold": self.wolfpack_dc_hold_var.get(),
            "wolfpack_dc_gap": self.wolfpack_dc_gap_var.get(),
        }

    def _set_triggernade_settings(self, data):
        """Apply triggernade settings from dict"""
        if "triggernade_hotkey" in data: self.triggernade_hotkey_var.set(data["triggernade_hotkey"])
        if "triggernade_repeat" in data: self.triggernade_repeat_var.set(data["triggernade_repeat"])
        if "triggernade_q_spam" in data: self.triggernade_q_spam_var.set(data["triggernade_q_spam"])
        if "trig_m1_hold" in data: self.trig_m1_hold_var.set(data["trig_m1_hold"])
        if "trig_m2_hold" in data: self.trig_m2_hold_var.set(data["trig_m2_hold"])
        if "trig_drag_speed" in data: self.trig_drag_speed_var.set(data["trig_drag_speed"])
        if "trig_dc_delay" in data: self.trig_dc_delay_var.set(data["trig_dc_delay"])
        if "trig_dc_throws" in data: self.trig_dc_throws_var.set(data["trig_dc_throws"])
        if "trig_throw_delay" in data: self.trig_throw_delay_var.set(data["trig_throw_delay"])
        if "trig_reconnect_after" in data: self.trig_reconnect_after_var.set(data["trig_reconnect_after"])
        if "wait_before_espam" in data: self.wait_before_espam_var.set(data["wait_before_espam"])
        if "espam_duration" in data: self.espam_duration_var.set(data["espam_duration"])
        if "trig_m1_before_interweave" in data: self.trig_m1_before_interweave_var.set(data["trig_m1_before_interweave"])
        if "wait_before_cycle" in data: self.wait_before_cycle_var.set(data["wait_before_cycle"])
        if "trig_slot_pos" in data and data["trig_slot_pos"]:
            self.trig_slot_pos = tuple(data["trig_slot_pos"])
            self.config["trig_slot_pos"] = data["trig_slot_pos"]
        if "trig_drop_pos" in data and data["trig_drop_pos"]:
            self.trig_drop_pos = tuple(data["trig_drop_pos"])
            self.config["trig_drop_pos"] = data["trig_drop_pos"]
        if self.trig_slot_pos and self.trig_drop_pos:
            self.trig_drag_var.set(f"Slot:{list(self.trig_slot_pos)} Drop:{list(self.trig_drop_pos)}")
        if "wolfpack_m1_hold" in data: self.wolfpack_m1_hold_var.set(data["wolfpack_m1_hold"])
        if "wolfpack_m1_gap" in data: self.wolfpack_m1_gap_var.set(data["wolfpack_m1_gap"])
        if "wolfpack_dc_hold" in data: self.wolfpack_dc_hold_var.set(data["wolfpack_dc_hold"])
        if "wolfpack_dc_gap" in data: self.wolfpack_dc_gap_var.set(data["wolfpack_dc_gap"])
        self.save_settings()

    def _get_mine_settings(self):
        """Get all mine dupe-related settings as a dict"""
        return {
            "mine_hotkey": self.mine_hotkey_var.get(),
            "mine_repeat": self.mine_repeat_var.get(),
            "mine_cook": self.mine_cook_var.get(),
            "mine_dc_delay": self.mine_dc_delay_var.get(),
            "mine_drag_speed": self.mine_drag_speed_var.get(),
            "mine_pre_close": self.mine_pre_close_var.get(),
            "mine_tab_hold": self.mine_tab_hold_var.get(),
            "mine_close_reconnect": self.mine_close_reconnect_var.get(),
            "mine_click_delay": self.mine_click_delay_var.get(),
            "mine_pickup_hold": self.mine_pickup_hold_var.get(),
            "mine_e_delay": self.mine_e_delay_var.get(),
            "mine_loop_delay": self.mine_loop_delay_var.get(),
            "mine_reselect": self.mine_reselect_var.get(),
            "mine_q_mode": self.mine_q_mode_var.get(),
            "mine_q_direction": self.mine_q_direction_var.get(),
            "mine_nudge": self.mine_nudge_var.get(),
            "mine_nudge_px": self.mine_nudge_px_var.get(),
            "mine_slot_pos": list(self.mine_slot_pos),
            "mine_drop_pos": list(self.mine_drop_pos),
        }

    def _set_mine_settings(self, data):
        """Apply mine dupe settings from dict"""
        if "mine_hotkey" in data: self.mine_hotkey_var.set(data["mine_hotkey"])
        if "mine_repeat" in data: self.mine_repeat_var.set(data["mine_repeat"])
        if "mine_cook" in data: self.mine_cook_var.set(data["mine_cook"])
        if "mine_dc_delay" in data: self.mine_dc_delay_var.set(data["mine_dc_delay"])
        if "mine_drag_speed" in data: self.mine_drag_speed_var.set(data["mine_drag_speed"])
        if "mine_pre_close" in data: self.mine_pre_close_var.set(data["mine_pre_close"])
        if "mine_tab_hold" in data: self.mine_tab_hold_var.set(data["mine_tab_hold"])
        if "mine_close_reconnect" in data: self.mine_close_reconnect_var.set(data["mine_close_reconnect"])
        if "mine_click_delay" in data: self.mine_click_delay_var.set(data["mine_click_delay"])
        if "mine_pickup_hold" in data: self.mine_pickup_hold_var.set(data["mine_pickup_hold"])
        if "mine_e_delay" in data: self.mine_e_delay_var.set(data["mine_e_delay"])
        if "mine_loop_delay" in data: self.mine_loop_delay_var.set(data["mine_loop_delay"])
        if "mine_reselect" in data: self.mine_reselect_var.set(data["mine_reselect"])
        if "mine_q_mode" in data: self.mine_q_mode_var.set(data["mine_q_mode"])
        if "mine_q_direction" in data:
            self.mine_q_direction_var.set(data["mine_q_direction"])
            self.mine_q_dir_btn.config(text=data["mine_q_direction"])
        if "mine_nudge" in data: self.mine_nudge_var.set(data["mine_nudge"])
        if "mine_nudge_px" in data: self.mine_nudge_px_var.set(data["mine_nudge_px"])
        if "mine_slot_pos" in data:
            self.mine_slot_pos = tuple(data["mine_slot_pos"])
            self.config["mine_slot_pos"] = data["mine_slot_pos"]
        if "mine_drop_pos" in data:
            self.mine_drop_pos = tuple(data["mine_drop_pos"])
            self.config["mine_drop_pos"] = data["mine_drop_pos"]
            self.mine_drag_var.set(f"Slot:{list(self.mine_slot_pos)} Drop:{list(self.mine_drop_pos)}")
        self.save_settings()

    def export_triggernade(self):
        """Export triggernade settings to file"""
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")],
                                            initialfile="triggernade_settings.json")
        if path:
            with open(path, 'w') as f:
                json.dump({"type": "triggernade", **self._get_triggernade_settings()}, f, indent=2)
            print(f"[EXPORT] Triggernade settings saved to {path}")

    def import_triggernade(self):
        """Import triggernade settings from file"""
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            with open(path, 'r') as f:
                data = json.load(f)
            self._set_triggernade_settings(data)
            self.register_hotkeys()
            print(f"[IMPORT] Triggernade settings loaded from {path}")

    def export_mine(self):
        """Export mine dupe settings to file"""
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")],
                                            initialfile="mine_settings.json")
        if path:
            with open(path, 'w') as f:
                json.dump({"type": "mine", **self._get_mine_settings()}, f, indent=2)
            print(f"[EXPORT] Mine settings saved to {path}")

    def import_mine(self):
        """Import mine dupe settings from file"""
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            with open(path, 'r') as f:
                data = json.load(f)
            self._set_mine_settings(data)
            self.register_hotkeys()
            print(f"[IMPORT] Mine settings loaded from {path}")

    def export_all_settings(self):
        """Export all macro settings to a single file"""
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")],
                                            initialfile="all_settings.json")
        if path:
            data = {
                "type": "all",
                "triggernade": self._get_triggernade_settings(),
                "mine": self._get_mine_settings(),
            }
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[EXPORT] All settings saved to {path}")

    def import_all_settings(self):
        """Import all macro settings from file"""
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            with open(path, 'r') as f:
                data = json.load(f)
            # Handle both single-macro and all-settings files
            if data.get("type") == "all":
                if "triggernade" in data: self._set_triggernade_settings(data["triggernade"])
                if "mine" in data: self._set_mine_settings(data["mine"])
            elif data.get("type") == "triggernade":
                self._set_triggernade_settings(data)
            elif data.get("type") == "mine":
                self._set_mine_settings(data)
            else:
                # Try to detect from keys
                if "triggernade_hotkey" in data: self._set_triggernade_settings(data)
                if "mine_hotkey" in data: self._set_mine_settings(data)
            self.register_hotkeys()
            print(f"[IMPORT] Settings loaded from {path}")

    def register_hotkeys(self):
        # Clear ALL hooks first to prevent ghost hotkeys (including on_press_key hooks)
        try:
            keyboard.unhook_all()
            print("[HOTKEY] Cleared all previous hotkeys and hooks")
        except Exception as e:
            print(f"[HOTKEY] Error clearing hotkeys: {e}")

        self.triggernade_hotkey_registered = None
        self.quickdrop_hotkey_registered = None
        self.espam_hotkey_registered = None
        self.escape_hotkey_registered = None
        self.dc_both_hotkey_registered = None
        self.dc_outbound_hotkey_registered = None
        self.dc_inbound_hotkey_registered = None
        self.tamper_hotkey_registered = None
        self.mine_hotkey_registered = None
        self.minimize_hotkey_registered = None
        self.tray_hotkey_registered = None
        self.reconnect_hotkey_registered = None
        # Alt+hotkey for re-recording positions
        self.trig_rerecord_registered = None
        self.mine_rerecord_registered = None

        # Register ALL hotkeys
        trig_hk = self.triggernade_hotkey_var.get()
        espam_hk = self.espam_hotkey_var.get()

        print(f"[HOTKEY] Registering hotkeys: triggernade='{trig_hk}', espam='{espam_hk}'")

        if trig_hk and trig_hk != "Press key...":
            try:
                self.triggernade_hotkey_registered = keyboard.add_hotkey(trig_hk, self.on_triggernade_hotkey, suppress=False)
                print(f"[HOTKEY] Triggernade registered OK: '{trig_hk}' -> {self.triggernade_hotkey_registered}")
            except Exception as e:
                print(f"[HOTKEY] FAILED triggernade '{trig_hk}': {e}")

        qd_hk = self.quickdrop_hotkey_var.get()
        if qd_hk and qd_hk != "Press key...":
            try:
                self.quickdrop_hotkey_registered = keyboard.add_hotkey(qd_hk, self.on_quickdrop_hotkey, suppress=False)
                print(f"[HOTKEY] QuickDrop registered OK: '{qd_hk}' -> {self.quickdrop_hotkey_registered}")
            except Exception as e:
                print(f"[HOTKEY] FAILED quickdrop '{qd_hk}': {e}")

        if espam_hk and espam_hk != "Press key...":
            try:
                self.espam_hotkey_registered = keyboard.add_hotkey(espam_hk, self.on_espam_hotkey, suppress=False)
                print(f"[HOTKEY] E-Spam registered OK: '{espam_hk}' -> {self.espam_hotkey_registered}")
            except Exception as e:
                print(f"[HOTKEY] FAILED espam '{espam_hk}': {e}")

        mine_hk = self.mine_hotkey_var.get()
        if mine_hk and mine_hk != "Press key...":
            try:
                self.mine_hotkey_registered = keyboard.add_hotkey(mine_hk, self.on_mine_hotkey, suppress=False)
                print(f"[HOTKEY] Mine registered OK: '{mine_hk}' -> {self.mine_hotkey_registered}")
            except Exception as e:
                print(f"[HOTKEY] FAILED mine '{mine_hk}': {e}")

        # Register quick disconnect hotkeys (use on_press_key so they work while other keys held)
        dc_both_hk = self.dc_both_hotkey_var.get()
        if dc_both_hk and dc_both_hk != "Press key..." and dc_both_hk != "...":
            try:
                self.dc_both_hotkey_registered = keyboard.on_press_key(dc_both_hk, lambda e: self.toggle_dc_both(), suppress=False)
                print(f"[HOTKEY] DC Both registered OK: '{dc_both_hk}' -> {self.dc_both_hotkey_registered}")
            except Exception as e:
                print(f"[HOTKEY] FAILED dc_both '{dc_both_hk}': {e}")

        dc_outbound_hk = self.dc_outbound_hotkey_var.get()
        if dc_outbound_hk and dc_outbound_hk != "Press key..." and dc_outbound_hk != "...":
            try:
                self.dc_outbound_hotkey_registered = keyboard.on_press_key(dc_outbound_hk, lambda e: self.toggle_dc_outbound(), suppress=False)
                print(f"[HOTKEY] DC Outbound registered OK: '{dc_outbound_hk}' -> {self.dc_outbound_hotkey_registered}")
            except Exception as e:
                print(f"[HOTKEY] FAILED dc_outbound '{dc_outbound_hk}': {e}")

        dc_inbound_hk = self.dc_inbound_hotkey_var.get()
        if dc_inbound_hk and dc_inbound_hk != "Press key..." and dc_inbound_hk != "...":
            try:
                self.dc_inbound_hotkey_registered = keyboard.on_press_key(dc_inbound_hk, lambda e: self.toggle_dc_inbound(), suppress=False)
                print(f"[HOTKEY] DC Inbound registered OK: '{dc_inbound_hk}' -> {self.dc_inbound_hotkey_registered}")
            except Exception as e:
                print(f"[HOTKEY] FAILED dc_inbound '{dc_inbound_hk}': {e}")

        tamper_hk = self.tamper_hotkey_var.get()
        if tamper_hk and tamper_hk != "Press key..." and tamper_hk != "...":
            try:
                self.tamper_hotkey_registered = keyboard.on_press_key(tamper_hk, lambda e: self.toggle_tamper(), suppress=False)
                print(f"[HOTKEY] Tamper registered OK: '{tamper_hk}' -> {self.tamper_hotkey_registered}")
            except Exception as e:
                print(f"[HOTKEY] FAILED tamper '{tamper_hk}': {e}")

        # Register minimize hotkey
        min_hk = self.minimize_hotkey_var.get()
        if min_hk and min_hk != "Press key...":
            try:
                self.minimize_hotkey_registered = keyboard.add_hotkey(min_hk, self.minimize_window, suppress=False)
                print(f"[HOTKEY] Minimize registered OK: '{min_hk}' -> {self.minimize_hotkey_registered}")
            except Exception as e:
                print(f"[HOTKEY] FAILED minimize '{min_hk}': {e}")

        # Register minimize to tray hotkey
        tray_hk = self.tray_hotkey_var.get()
        if tray_hk and tray_hk != "Press key...":
            try:
                self.tray_hotkey_registered = keyboard.add_hotkey(tray_hk, self.minimize_to_tray, suppress=False)
                print(f"[HOTKEY] Tray registered OK: '{tray_hk}' -> {self.tray_hotkey_registered}")
            except Exception as e:
                print(f"[HOTKEY] FAILED tray '{tray_hk}': {e}")

        # Register reconnect macro hotkey
        reconnect_hk = self.reconnect_hotkey_var.get()
        if reconnect_hk and reconnect_hk != "Press key...":
            try:
                self.reconnect_hotkey_registered = keyboard.add_hotkey(reconnect_hk, self.play_reconnect_macro, suppress=False)
                print(f"[HOTKEY] Reconnect macro registered OK: '{reconnect_hk}' -> {self.reconnect_hotkey_registered}")
            except Exception as e:
                print(f"[HOTKEY] FAILED reconnect '{reconnect_hk}': {e}")

        # Register configurable stop all hotkey
        stop_hk = self.stop_hotkey_var.get()
        if stop_hk and stop_hk != "Press key...":
            try:
                self.escape_hotkey_registered = keyboard.add_hotkey(stop_hk, self.stop_all_macros, suppress=False)
                print(f"[HOTKEY] Stop All registered OK: '{stop_hk}' -> {self.escape_hotkey_registered}")
            except Exception as e:
                print(f"[HOTKEY] FAILED stop all '{stop_hk}': {e}")

        # Register Alt+hotkey variants for quick position re-recording
        print("[HOTKEY] Registering Alt+hotkey re-record shortcuts...")

        # Triggernade: Alt+hotkey = re-record position
        if trig_hk and trig_hk != "Press key...":
            try:
                alt_trig_hk = f"alt+{trig_hk}" if not trig_hk.startswith("alt+") else trig_hk
                self.trig_rerecord_registered = keyboard.add_hotkey(alt_trig_hk, self.start_trig_drag_recording, suppress=False)
                print(f"[HOTKEY] Triggernade re-record registered: '{alt_trig_hk}'")
            except Exception as e:
                print(f"[HOTKEY] FAILED triggernade re-record '{alt_trig_hk}': {e}")

        # Mine: Alt+hotkey = re-record position
        if mine_hk and mine_hk != "Press key...":
            try:
                alt_mine_hk = f"alt+{mine_hk}" if not mine_hk.startswith("alt+") else mine_hk
                self.mine_rerecord_registered = keyboard.add_hotkey(alt_mine_hk, self.start_mine_drag_recording, suppress=False)
                print(f"[HOTKEY] Mine re-record registered: '{alt_mine_hk}'")
            except Exception as e:
                print(f"[HOTKEY] FAILED mine re-record '{alt_mine_hk}': {e}")

    def stop_all_macros(self):
        """Universal stop - triggered by configurable hotkey"""
        # Don't interrupt reconnect macro recording
        if getattr(self, '_reconnect_recording_active', False):
            print("[HOTKEY] Stop All pressed but reconnect recording active - ignoring")
            return
        print("[HOTKEY] Stop All pressed - stopping all macros!")
        self.triggernade_stop = True
        self.quickdrop_stop = True
        self.espam_stop = True
        self.mine_stop = True
        # Also cancel any active recordings
        self._drag_recording_cancelled = True
        self._mine_recording_cancelled = True
        self.root.after(0, lambda: self.show_overlay("Stopped"))

    def on_triggernade_hotkey(self):
        """Toggle triggernade macro"""
        if not self._triggernade_lock.acquire(blocking=False):
            return  # Already processing, ignore duplicate
        try:
            print(f"[HOTKEY] Triggernade hotkey PRESSED! running={self.triggernade_running}")
            if self.triggernade_running:
                print("[HOTKEY] Setting triggernade_stop = True")
                self.triggernade_stop = True
                self.root.after(0, lambda: self.triggernade_status_var.set("Stopping..."))
            else:
                print("[HOTKEY] Starting triggernade macro")
                # Reset ALL stop flags so vsleep doesn't exit early
                self.triggernade_stop = False
                self.mine_stop = False
                self.espam_stop = False
                self.triggernade_running = True
                self.root.after(0, lambda: self.triggernade_status_var.set("RUNNING"))
                self.root.after(0, lambda: self.triggernade_status_label.config(foreground="orange"))
                self.root.after(0, lambda: self.show_overlay("Wolfpack/Triggernade started"))
                threading.Thread(target=self.run_triggernade_macro, daemon=True).start()
        finally:
            self._triggernade_lock.release()

    def run_triggernade_macro(self):
        """
        Triggernade/Wolfpack macro
        Initial setup runs once, then wolfpack loop repeats if auto-loop enabled
        """
        repeat = self.triggernade_repeat_var.get()
        is_disconnected = False
        dc_key = None  # Initialize for finally block

        # Validate positions are recorded
        if not self.trig_drag_start or not self.trig_drag_end:
            self.root.after(0, lambda: self.show_overlay("Record drag positions first!", force=True))
            self.triggernade_running = False
            self.root.after(0, lambda: self.triggernade_status_var.set("Ready"))
            self.root.after(0, lambda: self.triggernade_status_label.config(foreground="gray"))
            return

        # Validate DC Both hotkey is set if looping is enabled
        if repeat and not self.dc_both_hotkey_var.get():
            self.root.after(0, lambda: self.show_overlay("Set DC Both hotkey to use Wolfpack loop!", force=True))
            self.triggernade_running = False
            self.root.after(0, lambda: self.triggernade_status_var.set("Ready"))
            self.root.after(0, lambda: self.triggernade_status_label.config(foreground="gray"))
            return

        print(f"[TRIGGERNADE] Using positions: {self.trig_drag_start} → {self.trig_drag_end}")

        # Release ALL buttons and keys before starting
        pynput_mouse.release(MouseButton.left)
        pynput_mouse.release(MouseButton.left)
        pynput_mouse.release(MouseButton.right)
        pynput_keyboard.release('e')
        pynput_keyboard.release('q')
        pynput_keyboard.release(Key.tab)

        # Brief delay so starting hotkey doesn't trigger stop
        time.sleep(0.2)

        try:
            # ===== INITIAL SETUP (runs once) =====
            print(f"\n{'='*50}")
            print(f"INITIAL SETUP")
            print(f"{'='*50}")

            # ===== Left click throw (configurable) =====
            m1_hold = self.trig_m1_hold_var.get()
            m2_hold = self.trig_m2_hold_var.get()

            pynput_mouse.press(MouseButton.left)
            self.vsleep(m1_hold)

            # ===== Right click during throw (configurable) =====
            pynput_mouse.press(MouseButton.right)
            self.vsleep(m2_hold)
            pynput_mouse.release(MouseButton.right)
            print(f"Throw (M1:{m1_hold}ms) + M2:{m2_hold}ms")

            pynput_mouse.release(MouseButton.left)

            # ===== Delay before disconnect =====
            dc_delay = self.trig_dc_delay_var.get()
            if dc_delay > 0:
                self.vsleep(dc_delay)

            if self.triggernade_stop:
                return

            # ===== Disconnect (outbound only for triggernade) =====
            start_packet_drop(inbound=False)
            is_disconnected = True
            self.vsleep(51)
            print(f"Disconnected (outbound only)")

            if self.triggernade_stop:
                return

            # ===== TAB to open inventory 51ms =====
            self.vsleep(20)
            pynput_keyboard.press(Key.tab)
            self.vsleep(301)
            pynput_keyboard.release(Key.tab)
            print(f"Inventory opened")

            if self.triggernade_stop:
                return

            # ===== Wait then drop via curved drag =====
            self.vsleep(120)
            pynput_mouse.release(MouseButton.left)
            pynput_mouse.position = self.trig_drag_start
            self.vsleep(30)
            pynput_mouse.press(MouseButton.left)
            self.vsleep(50)
            drag_speed = self.trig_drag_speed_var.get()
            self.curved_drag(self.trig_drag_start, self.trig_drag_end, steps=25, step_delay=drag_speed)
            pynput_mouse.release(MouseButton.left)
            print(f"Dropped with curved drag")

            if self.triggernade_stop:
                return

            # ===== Wait then TAB close =====
            self.vsleep(self.drag_wait_after)

            pynput_keyboard.press(Key.tab)
            self.vsleep(51)
            pynput_keyboard.release(Key.tab)
            print(f"Inventory closed")

            if self.triggernade_stop:
                return

            # ===== Reconnect =====
            stop_packet_drop()
            is_disconnected = False
            print(f"Reconnected - Initial setup complete")

            # ===== E spam + clicking to grab the falling object =====
            # Fast burst to reliably grab the dropped item
            print(f"Grabbing falling object...")
            for _ in range(15):  # 15 fast cycles (~450ms total)
                pynput_keyboard.press('e')
                time.sleep(0.005)
                pynput_keyboard.release('e')
                pynput_mouse.press(MouseButton.left)
                time.sleep(0.015)
                pynput_mouse.release(MouseButton.left)
                time.sleep(0.010)
            print(f"Starting wolfpack loop!")

            # ===== WOLFPACK LOOP SECTION =====
            # G Hub macro pattern: click spam + periodic DC for ~186ms
            # One loop = ~8 clicks (~1000ms) + DC for ~186ms while clicking + reconnect
            # Only checks stop flag at END of each loop iteration

            # Get user's DC Both hotkey and convert to pynput key
            dc_hotkey_str = self.dc_both_hotkey_var.get()
            special_keys = {
                'shift': Key.shift, 'ctrl': Key.ctrl, 'alt': Key.alt,
                'space': Key.space, 'enter': Key.enter, 'tab': Key.tab,
                'backspace': Key.backspace, 'delete': Key.delete,
                'esc': Key.esc, 'escape': Key.esc,
                'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right,
                'home': Key.home, 'end': Key.end, 'page_up': Key.page_up, 'page_down': Key.page_down,
                'insert': Key.insert, 'pause': Key.pause,
                'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
                'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
                'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
            }
            dc_key = special_keys.get(dc_hotkey_str.lower(), dc_hotkey_str) if dc_hotkey_str else None

            if not dc_key:
                print("[WOLFPACK] ERROR: No DC Both hotkey configured!")
                return

            print(f"[WOLFPACK] Using DC hotkey: {dc_hotkey_str}")

            # Get timing from UI vars (in ms), convert to seconds
            m1_hold = self.wolfpack_m1_hold_var.get() / 1000.0
            m1_gap = self.wolfpack_m1_gap_var.get() / 1000.0
            dc_hold = self.wolfpack_dc_hold_var.get() / 1000.0
            dc_gap = self.wolfpack_dc_gap_var.get() / 1000.0

            print(f"[WOLFPACK] M1: {m1_hold*1000:.0f}ms hold, {m1_gap*1000:.0f}ms gap")
            print(f"[WOLFPACK] DC: {dc_hold*1000:.0f}ms hold, {dc_gap*1000:.0f}ms gap")

            # Continuous click thread
            click_running = [True]
            def click_loop():
                while click_running[0]:
                    pynput_mouse.press(MouseButton.left)
                    time.sleep(m1_hold)
                    pynput_mouse.release(MouseButton.left)
                    time.sleep(m1_gap)

            click_thread = threading.Thread(target=click_loop, daemon=True)
            click_thread.start()

            # Even DC cycle
            while True:
                pynput_keyboard.press(dc_key)
                is_disconnected = True
                time.sleep(dc_hold)
                pynput_keyboard.release(dc_key)
                is_disconnected = False

                if self.triggernade_stop:
                    click_running[0] = False
                    # Ensure reconnected - release DC key and force stop packet drop
                    pynput_keyboard.release(dc_key)
                    time.sleep(0.1)
                    stop_packet_drop()
                    is_disconnected = False
                    break

                time.sleep(dc_gap)

        finally:
            # Release ALL buttons and keys
            pynput_mouse.release(MouseButton.left)
            pynput_mouse.release(MouseButton.left)
            pynput_mouse.release(MouseButton.right)
            pynput_keyboard.release('e')
            pynput_keyboard.release('q')
            pynput_keyboard.release(Key.tab)

            # Release DC hotkey if it was set and pressed
            if dc_key is not None:
                try:
                    pynput_keyboard.release(dc_key)
                except Exception:
                    pass

            if is_disconnected:
                stop_packet_drop()
            self.triggernade_running = False
            self.triggernade_stop = False
            self.root.after(0, lambda: self.triggernade_status_var.set("Ready"))
            self.root.after(0, lambda: self.triggernade_status_label.config(foreground="gray"))
            self.root.after(0, lambda: self.show_overlay("Wolfpack stopped."))

    def on_quickdrop_hotkey(self):
        """Toggle quick drop macro (no DC version)"""
        if not self._quickdrop_lock.acquire(blocking=False):
            return
        try:
            print(f"[HOTKEY] QuickDrop hotkey PRESSED! running={self.quickdrop_running}")
            if self.quickdrop_running:
                print("[HOTKEY] Setting quickdrop_stop = True")
                self.quickdrop_stop = True
                self.root.after(0, lambda: self.quickdrop_status_var.set("Stopping..."))
            else:
                print("[HOTKEY] Starting quickdrop macro")
                self.quickdrop_stop = False
                self.quickdrop_running = True
                self.root.after(0, lambda: self.quickdrop_status_var.set("RUNNING"))
                self.root.after(0, lambda: self.quickdrop_status_label.config(foreground="orange"))
                self.root.after(0, lambda: self.show_overlay("Quick Drop started"))
                threading.Thread(target=self.run_quickdrop_macro, daemon=True).start()
        finally:
            self._quickdrop_lock.release()

    def run_quickdrop_macro(self):
        """
        Quick drop macro - same as triggernade but NO DISCONNECT
        Uses right-click context menu -> drop to ground (super fast)
        """
        repeat = self.quickdrop_repeat_var.get()
        cycle = 0

        # Get cook time from triggernade settings (same timing)
        cook_time = self.trig_m1_hold_var.get() / 1000.0

        print(f"[QUICKDROP] Starting - cook={cook_time}s, repeat={repeat}")
        print(f"[QUICKDROP] Positions: R:{self.quickdrop_rclick_pos} L:{self.quickdrop_lclick_pos}")

        try:
            while True:
                cycle += 1
                print(f"[QUICKDROP] === Cycle {cycle} ===")

                if self.quickdrop_stop:
                    print("[QUICKDROP] Stop detected at cycle start")
                    break

                # ===== COOK: Hold M1 =====
                print(f"[QUICKDROP] M1 down (cook {cook_time}s)")
                pynput_mouse.press(pynput.mouse.Button.left)
                time.sleep(cook_time)
                pynput_mouse.release(pynput.mouse.Button.left)
                print("[QUICKDROP] M1 up")

                if self.quickdrop_stop:
                    break

                # ===== OPEN INVENTORY =====
                pynput_keyboard.press(pynput.keyboard.Key.tab)
                time.sleep(0.01)
                pynput_keyboard.release(pynput.keyboard.Key.tab)
                print("[QUICKDROP] TAB (inventory)")

                # Almost no delay - super fast
                time.sleep(0.05)

                if self.quickdrop_stop:
                    break

                # ===== RIGHT-CLICK on item (context menu) =====
                rx, ry = self.quickdrop_rclick_pos
                pynput_mouse.position = (rx, ry)
                time.sleep(0.01)
                pynput_mouse.press(pynput.mouse.Button.right)
                time.sleep(0.01)
                pynput_mouse.release(pynput.mouse.Button.right)
                print(f"[QUICKDROP] Right-click at ({rx}, {ry})")

                # Tiny delay for context menu
                time.sleep(0.02)

                # ===== LEFT-CLICK "Drop to Ground" =====
                lx, ly = self.quickdrop_lclick_pos
                pynput_mouse.position = (lx, ly)
                time.sleep(0.01)
                pynput_mouse.press(pynput.mouse.Button.left)
                time.sleep(0.01)
                pynput_mouse.release(pynput.mouse.Button.left)
                print(f"[QUICKDROP] Left-click at ({lx}, {ly})")

                if self.quickdrop_stop:
                    break

                # ===== CLOSE INVENTORY =====
                time.sleep(0.02)
                pynput_keyboard.press(pynput.keyboard.Key.esc)
                time.sleep(0.01)
                pynput_keyboard.release(pynput.keyboard.Key.esc)
                print("[QUICKDROP] ESC (close inventory)")

                # No delay after closing
                time.sleep(0.02)

                if self.quickdrop_stop:
                    break

                # Check repeat
                if not repeat:
                    print("[QUICKDROP] Single run complete")
                    break

                print(f"[QUICKDROP] Cycle {cycle} complete, repeating...")

        finally:
            self.quickdrop_running = False
            self.quickdrop_stop = False
            self.root.after(0, lambda: self.quickdrop_status_var.set("Ready"))
            self.root.after(0, lambda: self.quickdrop_status_label.config(foreground="gray"))
            self.root.after(0, lambda: self.show_overlay("Quick Drop stopped."))

    def on_mine_hotkey(self):
        """Toggle mine dupe macro"""
        if not self._mine_lock.acquire(blocking=False):
            return  # Already processing, ignore duplicate
        try:
            print(f"[HOTKEY] Mine hotkey PRESSED! running={self.mine_running}")
            if self.mine_running:
                print("[HOTKEY] Setting mine_stop = True")
                self.mine_stop = True
                self.root.after(0, lambda: self.mine_status_var.set("Stopping..."))
            else:
                print("[HOTKEY] Starting mine macro")
                # Reset ALL stop flags so vsleep doesn't exit early
                self.mine_stop = False
                self.triggernade_stop = False
                self.espam_stop = False
                self.mine_running = True
                self.root.after(0, lambda: self.mine_status_var.set("RUNNING"))
                self.root.after(0, lambda: self.mine_status_label.config(foreground="orange"))
                self.root.after(0, lambda: self.show_overlay("Mine Dupe started"))
                threading.Thread(target=self.run_mine_macro, daemon=True).start()
        finally:
            self._mine_lock.release()

    def run_mine_macro(self):
        """
        Mine dupe macro:
        1. M1 hold (place mine - configurable cook time)
        2. TAB to open inventory + Disconnect almost together
        3. Drag item to drop
        4. TAB close inventory
        5. Reconnect
        6. Click to pick up
        """
        repeat = self.mine_repeat_var.get()
        is_disconnected = False
        cycle = 0

        print(f"[MINE] Using drag: {self.mine_drag_start} → {self.mine_drag_end}")

        # Release all buttons before starting
        pynput_mouse.release(MouseButton.left)
        pynput_mouse.release(MouseButton.right)
        pynput_keyboard.release(Key.tab)

        hotkey = self.mine_hotkey_var.get()
        time.sleep(0.2)

        try:
            while True:
                if self.mine_stop:
                    print("[MINE] Stop detected at cycle start")
                    break
                if hotkey and keyboard.is_pressed(hotkey):
                    print("[MINE] Hotkey pressed - stopping")
                    self.mine_stop = True
                    break

                cycle += 1
                print(f"\n{'='*50}")
                print(f"MINE CYCLE {cycle}")
                print(f"{'='*50}")

                # Read all timing values ONCE at cycle start
                cook_time = self.mine_cook_var.get()
                dc_delay = self.mine_dc_delay_var.get()
                click_delay = self.mine_click_delay_var.get()
                dupe_click_hold = self.mine_pickup_hold_var.get()
                e_delay = self.mine_e_delay_var.get()
                loop_delay = self.mine_loop_delay_var.get()
                tab_hold = self.mine_tab_hold_var.get()
                close_reconnect = self.mine_close_reconnect_var.get()
                pre_close = self.mine_pre_close_var.get()
                print(f"[{cycle}] Timings: cook={cook_time}, dc_delay={dc_delay}, click_delay={click_delay}, dupe_hold={dupe_click_hold}")

                # Removed cycle overlay - was causing Windows beep
                # self.root.after(0, lambda c=cycle: self.show_overlay(f"Mine {c}"))

                # ===== YOUR EXACT SEQUENCE (from your successful recordings) =====
                # Key insight: TAB and DC happen WHILE still holding M1 (cooking)

                # Clean state
                pynput_mouse.release(MouseButton.left)
                self.vsleep(50)

                # 1. M1 PRESS (start cooking mine)
                print(f"[{cycle}] M1 press - cooking for {cook_time}ms...")
                pynput_mouse.press(MouseButton.left)

                # 2. Cook time: wait before TAB press (open inventory while still holding M1!)
                self.vsleep(cook_time)
                pynput_keyboard.press(Key.tab)
                print(f"[{cycle}] TAB press after {cook_time}ms cook (inventory opening, M1 still held)")

                # 3. DC delay: wait before DC (while still holding M1!)
                self.vsleep(dc_delay)
                start_packet_drop(inbound=False)
                is_disconnected = True
                print(f"[{cycle}] DC started after {dc_delay}ms (M1 still held)")

                # 4. ~24ms later: TAB release
                self.vsleep(24)
                pynput_keyboard.release(Key.tab)
                print(f"[{cycle}] TAB release")

                # 5. ~326ms later: M1 release
                self.vsleep(326)
                pynput_mouse.release(MouseButton.left)
                print(f"[{cycle}] M1 release - cook done")

                if self.mine_stop:
                    break

                # 6. Start drag (with variance)
                self.vsleep(200 + random.randint(0, 100))  # 200-300ms wait
                pynput_mouse.position = self.mine_drag_start
                self.vsleep(30 + random.randint(0, 20))
                pynput_mouse.press(MouseButton.left)

                # 7. Drag with varied speed
                drag_speed = self.mine_drag_speed_var.get()
                varied_speed = drag_speed + random.randint(-2, 2)  # Vary speed slightly
                self.curved_drag(self.mine_drag_start, self.mine_drag_end, steps=25, step_delay=max(3, varied_speed))
                pynput_mouse.release(MouseButton.left)
                print(f"[{cycle}] Drag complete")

                if self.mine_stop:
                    break

                # 8. TAB close after drag
                self.vsleep(pre_close)
                pynput_keyboard.press(Key.tab)
                self.vsleep(tab_hold)
                pynput_keyboard.release(Key.tab)
                print(f"[{cycle}] Inventory closed (pre_close={pre_close}, tab_hold={tab_hold})")

                if self.mine_stop:
                    break

                # 9. Wait then RECONNECT
                self.vsleep(close_reconnect)
                stop_packet_drop()
                is_disconnected = False
                print(f"[{cycle}] Reconnected")

                # 10. Wait then M1 click (uses click_delay slider)
                time.sleep(click_delay / 1000.0)
                dupe_click_hold = self.mine_pickup_hold_var.get()
                pynput_mouse.press(MouseButton.left)
                print(f"[{cycle}] M1 press after {click_delay}ms (holding {dupe_click_hold}ms)")

                # 11. Hold for dupe - use direct sleep, no variance/interruption
                time.sleep(dupe_click_hold / 1000.0)
                pynput_mouse.release(MouseButton.left)
                print(f"[{cycle}] M1 release after {dupe_click_hold}ms hold")
                print(f"[{cycle}] CYCLE DONE")

                if not repeat:
                    print(f"[{cycle}] Single cycle done")
                    break

                if self.mine_stop:
                    break

                # ===== LOOP ONLY: Pause, then E to pick up, then Q to swap =====
                self.vsleep(e_delay)

                # Single E press to pick up
                pynput_keyboard.press('e')
                self.vsleep(50)
                pynput_keyboard.release('e')
                print(f"[{cycle}] E pressed to pick up")

                if self.mine_stop:
                    break

                # Mouse nudge FIRST to avoid mines stacking
                if self.mine_nudge_var.get():
                    nudge_px = self.mine_nudge_px_var.get()
                    class MOUSEINPUT(ctypes.Structure):
                        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong),
                                    ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
                    class INPUT(ctypes.Structure):
                        _fields_ = [("type", ctypes.c_ulong), ("mi", MOUSEINPUT)]
                    MOUSEEVENTF_MOVE = 0x0001
                    inp = INPUT(type=0, mi=MOUSEINPUT(dx=nudge_px, dy=0, mouseData=0, dwFlags=MOUSEEVENTF_MOVE, time=0, dwExtraInfo=None))
                    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
                    print(f"[{cycle}] Nudged mouse {nudge_px}px right")

                # Q to swap back to mine in quick use
                self.vsleep(100)
                if self.mine_reselect_var.get():
                    q_mode = self.mine_q_mode_var.get()
                    if q_mode == "radial":
                        # Use direction-based radial selection
                        self._play_mine_q_radial()
                        print(f"[{cycle}] Q radial reselect ({self.mine_q_direction_var.get()})")
                    else:
                        # Simple Q tap
                        pynput_keyboard.press('q')
                        self.vsleep(50)
                        pynput_keyboard.release('q')
                        print(f"[{cycle}] Q tap to reselect")

                # Wait before next cycle (scales with variance slider - more extreme)
                loop_delay_ms = self.mine_loop_delay_var.get()
                variance_pct = self.timing_variance_var.get()
                extra_loop_var = random.uniform(0, variance_pct * 10) if variance_pct > 0 else 0
                self.vsleep(loop_delay_ms + extra_loop_var)

        finally:
            pynput_mouse.release(MouseButton.left)
            pynput_keyboard.release(Key.tab)
            if is_disconnected:
                stop_packet_drop()
            self.mine_running = False
            self.mine_stop = False
            self.root.after(0, lambda: self.mine_status_var.set("Ready"))
            self.root.after(0, lambda: self.mine_status_label.config(foreground="gray"))
            self.root.after(0, lambda: self.show_overlay("Mine Dupe stopped."))

    def on_espam_hotkey(self):
        """Toggle E-spam macro"""
        if not self._espam_lock.acquire(blocking=False):
            return  # Already processing, ignore duplicate
        try:
            print(f"[HOTKEY] E-Spam hotkey PRESSED! running={self.espam_running}")
            if self.espam_running:
                print("[HOTKEY] Setting espam_stop = True")
                self.espam_stop = True
                self.root.after(0, lambda: self.espam_status_var.set("Stopping..."))
            else:
                print("[HOTKEY] Starting E-spam macro")
                # Reset ALL stop flags so vsleep doesn't exit early
                self.espam_stop = False
                self.mine_stop = False
                self.triggernade_stop = False
                self.espam_running = True
                self.root.after(0, lambda: self.espam_status_var.set("SPAMMING E"))
                self.root.after(0, lambda: self.espam_status_label.config(foreground="green"))
                self.root.after(0, lambda: self.show_overlay("E-Spam running..."))
                threading.Thread(target=self.run_espam_macro, daemon=True).start()
        finally:
            self._espam_lock.release()

    def run_espam_macro(self):
        """E-Spam macro - spams E with configurable repeat delay"""
        from pynput.keyboard import Controller as KeyboardController
        kb = KeyboardController()

        # Brief delay so starting hotkey doesn't trigger stop
        time.sleep(0.2)

        repeat_delay_ms = self.espam_repeat_delay_var.get()  # now in ms

        try:
            while not self.espam_stop:
                # Spam E
                kb.press('e')
                self.vsleep(11)
                kb.release('e')
                self.vsleep(50)

                # If repeat delay > 0, pause between spam bursts
                if repeat_delay_ms > 0 and not self.espam_stop:
                    self.vsleep(repeat_delay_ms)
        finally:
            self.espam_running = False
            self.espam_stop = False
            self.root.after(0, lambda: self.espam_status_var.set("Ready"))
            self.root.after(0, lambda: self.espam_status_label.config(foreground="gray"))
            self.root.after(0, lambda: self.show_overlay("E-Spam stopped."))

    def show_overlay(self, text, force=False):
        if not force and not self.show_overlay_var.get():
            return
        if self.overlay_window is None or not self.overlay_window.winfo_exists():
            self.overlay_window = tk.Toplevel(self.root)
            self.overlay_window.overrideredirect(True)
            self.overlay_window.attributes('-topmost', True)
            self.overlay_window.attributes('-transparentcolor', 'black')
            self.overlay_window.attributes('-disabled', True)  # Prevent focus steal
            self.overlay_window.configure(bg='black')
            self.overlay_window.bell = lambda: None  # Disable bell on overlay
            self.overlay_window.bind('<Key>', lambda e: 'break')  # Eat all key events to prevent beep

            # Windows: Set WS_EX_NOACTIVATE to prevent focus stealing
            self.overlay_window.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.overlay_window.winfo_id())
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_APPWINDOW = 0x00040000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = style | WS_EX_NOACTIVATE
            style = style & ~WS_EX_APPWINDOW  # Also hide from taskbar
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

            # Use canvas for text with outline
            self.overlay_canvas = tk.Canvas(self.overlay_window, bg='black', highlightthickness=0)
            self.overlay_canvas.pack()

        # Clear and redraw
        self.overlay_canvas.delete('all')
        font = ("Arial", 48, "bold")

        # Measure text first
        temp_id = self.overlay_canvas.create_text(0, 0, text=text, font=font, anchor='nw')
        bbox = self.overlay_canvas.bbox(temp_id)
        self.overlay_canvas.delete(temp_id)

        if bbox:
            w, h = bbox[2] - bbox[0] + 40, bbox[3] - bbox[1] + 40
            cx, cy = w // 2, h // 2
            self.overlay_canvas.config(width=w, height=h)

            # Draw black outline (offset in 8 directions)
            for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2), (-2,0), (2,0), (0,-2), (0,2)]:
                self.overlay_canvas.create_text(cx+dx, cy+dy, text=text, font=font, fill='black')
            # Draw white text on top
            self.overlay_canvas.create_text(cx, cy, text=text, font=font, fill='white')

        self.overlay_window.update_idletasks()

        # Center on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        overlay_width = self.overlay_window.winfo_reqwidth()
        overlay_height = self.overlay_window.winfo_reqheight()
        x = (screen_width - overlay_width) // 2
        y = (screen_height - overlay_height) // 2
        self.overlay_window.geometry(f"+{x}+{y}")
        self.overlay_window.deiconify()

        if self.overlay_hide_id:
            self.root.after_cancel(self.overlay_hide_id)
        self.overlay_hide_id = self.root.after(3000, self.hide_overlay)

    def hide_overlay(self):
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.withdraw()

    def on_close(self):
        self.triggernade_stop = True
        self.espam_stop = True
        self.mine_stop = True

        # ALWAYS ensure network is restored on close
        try:
            stop_packet_drop()
            stop_packet_tamper()
            print("[CLOSE] Network restored")
        except Exception as e:
            print(f"[CLOSE] Error restoring network: {e}")

        # Stop drag recording listener if active
        if self.drag_mouse_listener:
            try:
                self.drag_mouse_listener.stop()
            except:
                pass
        if self.triggernade_hotkey_registered:
            try:
                keyboard.remove_hotkey(self.triggernade_hotkey_registered)
            except:
                pass
        if self.espam_hotkey_registered:
            try:
                keyboard.remove_hotkey(self.espam_hotkey_registered)
            except:
                pass

        # Save window position
        self.config["window_x"] = self.root.winfo_x()
        self.config["window_y"] = self.root.winfo_y()
        save_config(self.config)

        self.root.destroy()


if __name__ == "__main__":
    try:
        # Obfuscation: rename exe to UUID name on first run (if enabled)
        rename_self_and_restart()

        # Make app DPI-aware so mouse coordinates are consistent
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
        except:
            try:
                ctypes.windll.user32.SetProcessDPIAware()  # Fallback
            except:
                pass

        if not is_admin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()

        print("=" * 50)
        print(f"{APP_NAME} Starting...")
        if OBFUSCATION_ENABLED:
            print(f"[OBFUS] Build ID: {BUILD_ID}")
        print("=" * 50)

        root = tk.Tk()
        app = QuickDupeApp(root)

        # Apply stay-on-top setting from config
        if app.config.get("stay_on_top", False):
            root.attributes('-topmost', True)
            print("[UI] Stay on top enabled from config")

        print(f"[CONFIG] Loaded config: {app.config}")

        app.register_hotkeys()
        print("[STARTUP] Ready - listening for hotkeys")
        print("=" * 50)

        root.mainloop()
    except Exception as e:
        import traceback
        print(f"CRASH ERROR: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")

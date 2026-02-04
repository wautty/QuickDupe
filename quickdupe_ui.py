import tkinter as tk
from tkinter import ttk, filedialog, colorchooser
import os
import sys
import math
import time
from PIL import Image, ImageTk

# quickdupe_ui.py
class QuickDupeUI:
    def __init__(self, app, root, colors, config):
        self.app = app  # Referenz zur Haupt-App
        self.root = root
        self.colors = colors
        self.config = config
    
    def setup_dark_theme(self):
        """Configure ttk styles for dark mode"""
        style = ttk.Style()
        style.theme_use("clam")

        # Configure colors
        style.configure(
            ".", background=self.colors["bg"], foreground=self.colors["text"]
        )
        style.configure("TFrame", background=self.colors["bg"])
        style.configure(
            "TLabel", background=self.colors["bg"], foreground=self.colors["text"]
        )
        style.configure(
            "TButton",
            background=self.colors["bg_light"],
            foreground=self.colors["text"],
            borderwidth=0,
            relief="flat",
            focuscolor="",
        )
        # Button hover uses darker accent
        accent_darker = self._darken_color(self.colors["highlight"], 50)
        style.map("TButton", background=[("active", accent_darker)])
        style.configure(
            "TCheckbutton",
            background=self.colors["bg"],
            foreground=self.colors["text"],
            indicatorbackground=self.colors["bg_light"],
            indicatorforeground=self.colors["text"],
            indicatorsize=16,
        )
        style.map("TCheckbutton", background=[("active", self.colors["bg"])])
        style.configure(
            "TEntry",
            fieldbackground=self.colors["bg_light"],
            foreground=self.colors["text"],
            borderwidth=0,
            relief="flat",
            padding=2,
        )
        bg_light = self.colors["bg_light"]
        bg_lighter = self.colors.get("bg_lighter", bg_light)
        style.configure(
            "TCombobox",
            fieldbackground=bg_light,
            background=bg_light,
            foreground=self.colors["text"],
            arrowcolor=self.colors["text"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", bg_light)],
            selectbackground=[("readonly", bg_lighter)],
            selectforeground=[("readonly", self.colors["text"])],
        )
        self.root.option_add("*TCombobox*Listbox.background", bg_light)
        self.root.option_add("*TCombobox*Listbox.foreground", self.colors["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", bg_lighter)
        self.root.option_add("*TCombobox*Listbox.selectForeground", self.colors["text"])
        # Separator uses much darker shade of accent
        accent_dark = self._darken_color(self.colors["highlight"], 80)
        style.configure("TSeparator", background=accent_dark)

        # Scrollbar styling - use 'alt' theme element (no grip lines)
        try:
            style.element_create("NoGrip.Scrollbar.thumb", "from", "alt")
            style.layout(  # type: ignore
                "NoGrip.Vertical.TScrollbar",
                [
                    (
                        "Vertical.Scrollbar.trough",
                        {
                            "sticky": "ns",
                            "children": [
                                (
                                    "NoGrip.Scrollbar.thumb",
                                    {"sticky": "nswe", "expand": True},
                                )
                            ],
                        },
                    )
                ], # pyright: ignore[reportArgumentType]
            )
        except:
            pass  # Already created
        style.configure(
            "NoGrip.Vertical.TScrollbar",
            background=bg_lighter,
            troughcolor=self.colors["bg"],
            borderwidth=0,
            relief="flat",
            width=10,
        )
        style.map(
            "NoGrip.Vertical.TScrollbar",
            background=[("active", bg_lighter), ("pressed", bg_lighter)],
        )

        # Scale (slider) styling - no grip lines, no outlines
        style.configure(
            "TScale",
            background=bg_lighter,
            troughcolor=bg_light,
            sliderlength=20,
            borderwidth=0,
            relief="flat",
            gripcount=0,
            lightcolor=bg_lighter,
            darkcolor=bg_lighter,
            bordercolor=bg_lighter,
            focuscolor="",
            highlightthickness=0,
        )
        style.configure(
            "Horizontal.TScale",
            background=bg_lighter,
            lightcolor=bg_lighter,
            darkcolor=bg_lighter,
            bordercolor=bg_lighter,
            troughcolor=bg_light,
        )

        # Section header style
        style.configure(
            "Header.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["highlight"],
            font=("Arial", 11, "bold"),
        )

        # Dim text style
        style.configure(
            "Dim.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["text_dim"],
        )

    def build_ui(self):
        # Custom title bar - store as instance var for color updates
        self.title_bar = tk.Frame(self.root, bg=self.colors["bg_light"], height=32)
        self.title_bar.pack(fill="x", side="top")
        self.title_bar.pack_propagate(False)
        title_bar = self.title_bar  # Local alias for convenience

        # Drag functionality (define first so we can use it)
        def start_drag(event):
            self._drag_x = event.x
            self._drag_y = event.y
            

    def build_ui(self):
        # Custom title bar - store as instance var for color updates
        self.title_bar = tk.Frame(self.root, bg=self.colors["bg_light"], height=32)
        self.title_bar.pack(fill="x", side="top")
        self.title_bar.pack_propagate(False)
        title_bar = self.title_bar  # Local alias for convenience

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
            if hasattr(self, "icon_image"):
                # Resize icon for title bar
                w, h = self.icon_image.width(), self.icon_image.height()
                factor = max(1, min(w, h) // 20)
                small_icon = self.icon_image.subsample(factor, factor)
                self.title_icon = small_icon  # Keep reference
                icon_label = tk.Label(
                    title_bar, image=small_icon, bg=self.colors["bg_light"]
                )
                icon_label.pack(side="left", padx=(8, 2))
                icon_label.bind("<Button-1>", start_drag)
                icon_label.bind("<B1-Motion>", drag)
        except:
            pass

        # Title label
        title_label = tk.Label(
            title_bar,
            text=APP_NAME,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            font=("Arial", 10, "bold"),
        )
        title_label.pack(side="left", padx=2)

        # Close button (rightmost)
        close_btn = tk.Label(
            title_bar,
            text=" ✕ ",
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            font=("Arial", 12),
            cursor="hand2",
        )
        close_btn.pack(side="right", padx=2)
        close_btn.bind("<Button-1>", lambda e: self.on_close())
        close_btn.bind(
            "<Enter>", lambda e: close_btn.config(bg=self.colors["highlight"])
        )
        close_btn.bind(
            "<Leave>", lambda e: close_btn.config(bg=self.colors["bg_light"])
        )

        # Minimize to tray button (down triangle) - middle
        tray_btn = tk.Label(
            title_bar,
            text=" ▼ ",
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            font=("Arial", 10),
            cursor="hand2",
        )
        tray_btn.pack(side="right", padx=2)
        tray_btn.bind("<Button-1>", lambda e: self.minimize_to_tray())
        tray_btn.bind("<Enter>", lambda e: tray_btn.config(bg=self.colors["accent"]))
        tray_btn.bind("<Leave>", lambda e: tray_btn.config(bg=self.colors["bg_light"]))

        # Minimize button (leftmost)
        min_btn = tk.Label(
            title_bar,
            text=" ─ ",
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            font=("Arial", 12),
            cursor="hand2",
        )
        min_btn.pack(side="right", padx=2)
        min_btn.bind("<Button-1>", lambda e: self.minimize_window())
        min_btn.bind("<Enter>", lambda e: min_btn.config(bg=self.colors["accent"]))
        min_btn.bind("<Leave>", lambda e: min_btn.config(bg=self.colors["bg_light"]))

        # Bind drag to title bar and label
        title_bar.bind("<Button-1>", start_drag)
        title_bar.bind("<B1-Motion>", drag)
        title_label.bind("<Button-1>", start_drag)
        title_label.bind("<B1-Motion>", drag)

        # Create main container with scrollbar
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        # Canvas for scrolling
        self.canvas = tk.Canvas(container, bg=self.colors["bg"], highlightthickness=0)

        # Custom minimal scrollbar using Canvas (no grip lines, clean look)
        self.scrollbar_canvas = tk.Canvas(
            container, width=10, bg=self.colors["bg"], highlightthickness=0, bd=0
        )
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
                self.scrollbar_canvas.delete("thumb")
                self.scrollbar_canvas.create_rectangle(
                    2,
                    thumb_top,
                    8,
                    thumb_top + thumb_height,
                    fill=self.colors.get("bg_lighter", self.colors["bg_light"]),
                    outline="",
                    tags="thumb",
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

        self.scrollbar_canvas.bind("<Button-1>", on_scrollbar_click)
        self.scrollbar_canvas.bind("<B1-Motion>", on_scrollbar_drag)
        self.scrollbar_canvas.bind("<ButtonRelease-1>", on_scrollbar_release)

        # Scrollable frame inside canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=update_scrollbar)

        # Make scrollable frame expand to canvas width so content can center
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)

        self.canvas.bind("<Configure>", on_canvas_configure)

        # Force initial width update after window is drawn
        def set_initial_width():
            self.canvas.update_idletasks()
            self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())

        self.root.after(50, set_initial_width)

        # Pack scrollbar and canvas
        self.scrollbar_canvas.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Enable mousewheel scrolling
        self.canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        # Build content in scrollable frame
        frame = self.scrollable_frame

        # ===== STAY ON TOP CHECKBOX =====
        self.stay_on_top_var = tk.BooleanVar(
            value=self.config.get("stay_on_top", False)
        )
        ttk.Checkbutton(
            frame,
            text="Stay on top",
            variable=self.stay_on_top_var,
            command=self.toggle_stay_on_top,
        ).pack(anchor="w", padx=10, pady=5)

        # ===== SHOW OVERLAY CHECKBOX =====
        self.show_overlay_var = tk.BooleanVar(
            value=self.config.get("show_overlay", True)
        )
        ttk.Checkbutton(
            frame,
            text="Show on-screen text",
            variable=self.show_overlay_var,
            command=self.save_settings,
        ).pack(anchor="w", padx=10, pady=5)

        # ===== TIMING VARIANCE SLIDER =====
        variance_frame = ttk.Frame(frame)
        variance_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(variance_frame, text="Timing variance:").pack(side="left")
        self.timing_variance_var = tk.IntVar(
            value=self.config.get("timing_variance", 0)
        )
        variance_slider = ttk.Scale(
            variance_frame,
            from_=0,
            to=20,
            orient="horizontal",
            variable=self.timing_variance_var,
            length=100,
            command=lambda v: self.save_settings(),
        )
        variance_slider.pack(side="left", padx=5)
        self.variance_label = ttk.Label(
            variance_frame, text=f"±{self.timing_variance_var.get()}%"
        )
        self.variance_label.pack(side="left")
        self.timing_variance_var.trace_add(
            "write",
            lambda *args: self.variance_label.config(
                text=f"±{self.timing_variance_var.get()}%"
            ),
        )

        # Drag timing values
        self.drag_wait_after = 300  # ms after drop before Tab close

        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=10)

        # ===== QUICK DISCONNECT SECTION =====
        ttk.Label(frame, text="── Quick Disconnect ──", style="Header.TLabel").pack(
            pady=(5, 5)
        )

        # DC Both (In+Out) row
        dc_both_frame = ttk.Frame(frame)
        dc_both_frame.pack(fill="x", padx=10, pady=2)
        self.dc_both_btn = tk.Button(
            dc_both_frame,
            text="DC BOTH",
            width=12,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            activebackground=self.colors["highlight"],
            activeforeground="white",
            bd=0,
            command=self.toggle_dc_both,
        )
        self.dc_both_btn.pack(side="left")
        ttk.Label(dc_both_frame, text="Hotkey:").pack(side="left", padx=(10, 0))
        self.dc_both_hotkey_var = tk.StringVar(
            value=self.config.get("dc_both_hotkey", "")
        )
        self.dc_both_hotkey_entry = tk.Entry(
            dc_both_frame,
            textvariable=self.dc_both_hotkey_var,
            width=10,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.dc_both_hotkey_entry.pack(side="left", padx=5)
        self.dc_both_record_btn = ttk.Button(
            dc_both_frame, text="Set", width=4, command=self.start_recording_dc_both
        )
        self.dc_both_record_btn.pack(side="left")

        # DC Outbound Only row
        dc_out_frame = ttk.Frame(frame)
        dc_out_frame.pack(fill="x", padx=10, pady=2)
        self.dc_outbound_btn = tk.Button(
            dc_out_frame,
            text="DC OUTBOUND",
            width=12,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            activebackground=self.colors["highlight"],
            activeforeground="white",
            bd=0,
            command=self.toggle_dc_outbound,
        )
        self.dc_outbound_btn.pack(side="left")
        ttk.Label(dc_out_frame, text="Hotkey:").pack(side="left", padx=(10, 0))
        self.dc_outbound_hotkey_var = tk.StringVar(
            value=self.config.get("dc_outbound_hotkey", "")
        )
        self.dc_outbound_hotkey_entry = tk.Entry(
            dc_out_frame,
            textvariable=self.dc_outbound_hotkey_var,
            width=10,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.dc_outbound_hotkey_entry.pack(side="left", padx=5)
        self.dc_outbound_record_btn = ttk.Button(
            dc_out_frame, text="Set", width=4, command=self.start_recording_dc_outbound
        )
        self.dc_outbound_record_btn.pack(side="left")

        # DC Inbound Only row
        dc_in_frame = ttk.Frame(frame)
        dc_in_frame.pack(fill="x", padx=10, pady=2)
        self.dc_inbound_btn = tk.Button(
            dc_in_frame,
            text="DC INBOUND",
            width=12,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            activebackground=self.colors["highlight"],
            activeforeground="white",
            bd=0,
            command=self.toggle_dc_inbound,
        )
        self.dc_inbound_btn.pack(side="left")
        ttk.Label(dc_in_frame, text="Hotkey:").pack(side="left", padx=(10, 0))
        self.dc_inbound_hotkey_var = tk.StringVar(
            value=self.config.get("dc_inbound_hotkey", "")
        )
        self.dc_inbound_hotkey_entry = tk.Entry(
            dc_in_frame,
            textvariable=self.dc_inbound_hotkey_var,
            width=10,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.dc_inbound_hotkey_entry.pack(side="left", padx=5)
        self.dc_inbound_record_btn = ttk.Button(
            dc_in_frame, text="Set", width=4, command=self.start_recording_dc_inbound
        )
        self.dc_inbound_record_btn.pack(side="left")

        # Tamper button (corrupts packets instead of dropping)
        tamper_frame = ttk.Frame(frame)
        tamper_frame.pack(fill="x", padx=10, pady=2)
        self.tamper_btn = tk.Button(
            tamper_frame,
            text="TAMPER",
            width=12,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            activebackground=self.colors["warning"],
            activeforeground="white",
            bd=0,
            command=self.toggle_tamper,
        )
        self.tamper_btn.pack(side="left")
        ttk.Label(tamper_frame, text="Hotkey:").pack(side="left", padx=(10, 0))
        self.tamper_hotkey_var = tk.StringVar(
            value=self.config.get("tamper_hotkey", "")
        )
        self.tamper_hotkey_entry = tk.Entry(
            tamper_frame,
            textvariable=self.tamper_hotkey_var,
            width=10,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.tamper_hotkey_entry.pack(side="left", padx=5)
        self.tamper_record_btn = ttk.Button(
            tamper_frame, text="Set", width=4, command=self.start_recording_tamper
        )
        self.tamper_record_btn.pack(side="left")
        tamper_info = ttk.Label(
            tamper_frame,
            text=" (?)",
            foreground=self.colors["text_dim"],
            cursor="hand2",
        )
        tamper_info.pack(side="left")
        self._add_tooltip(
            tamper_info,
            "Corrupts packets instead of dropping them.\nCan cause weird behavior instead of full DC.",
        )

        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=10)

        # ===== TRIGGERNADE SECTION =====
        trig_header = ttk.Frame(frame)
        trig_header.pack(pady=(5, 5))
        ttk.Label(
            trig_header, text="── Wolfpack/Triggernade Dupe ──", style="Header.TLabel"
        ).pack(side="left")
        trig_info = ttk.Label(
            trig_header, text=" (?)", foreground=self.colors["text_dim"], cursor="hand2"
        )
        trig_info.pack(side="left")
        self._add_tooltip(
            trig_info,
            "Record drag path from item slot to ground.\n\nMake sure inventory is full of items you're NOT duping (e.g. stacks of 1 ammo).\nFill safe pockets as well.\n\nQuick use slots must be empty EXCEPT item you're duping in first slot.\nEven utility slots must be empty.\n\nThen press Q to bring out wolfpack/triggernade/leaper pulse unit/other grenade and hit hotkey.\n\nTIP: Get it working SINGLE USE first. For auto-repeat, item must roll under your feet\nto be grabbed for looping. Drop piles of 1 of item you're duping around feet as backup copies to grab.\n\nTRIGGERNADES: Start with stack of 3 in first quick use slot - if it fails 2x it keeps going.\nTriggernades are unique: when picked up they return to the same stack.",
        )

        # Triggernade Hotkey row
        trig_hk = ttk.Frame(frame)
        trig_hk.pack(fill="x", padx=10, pady=5)
        ttk.Label(trig_hk, text="Hotkey:").pack(side="left")
        self.triggernade_hotkey_var = tk.StringVar(
            value=self.config.get("triggernade_hotkey", "")
        )
        self.triggernade_hotkey_entry = tk.Entry(
            trig_hk,
            textvariable=self.triggernade_hotkey_var,
            width=15,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.triggernade_hotkey_entry.pack(side="left", padx=5)
        self.triggernade_record_btn = ttk.Button(
            trig_hk, text="Set", width=6, command=self.start_recording_triggernade
        )
        self.triggernade_record_btn.pack(side="left", padx=5)

        # Triggernade drag record (works for both Xbox X and drag drop)
        trig_drag_frame = ttk.Frame(frame)
        trig_drag_frame.pack(fill="x", padx=10, pady=2)
        self.trig_drag_btn = ttk.Button(
            trig_drag_frame,
            text="Record",
            width=12,
            command=self.start_trig_drag_recording,
        )
        self.trig_drag_btn.pack(side="left")
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
        ttk.Label(
            trig_drag_frame, textvariable=self.trig_drag_var, font=("Consolas", 8)
        ).pack(side="left", padx=5)

        # Repeat checkbox
        self.triggernade_repeat_var = tk.BooleanVar(
            value=self.config.get("triggernade_repeat", False)
        )
        ttk.Checkbutton(
            frame,
            text="Auto (loop until pressed again)",
            variable=self.triggernade_repeat_var,
            command=self.save_settings,
        ).pack(anchor="w", padx=10, pady=5)

        # Q spam checkbox (optional re-equip between cycles)
        self.triggernade_q_spam_var = tk.BooleanVar(
            value=self.config.get("triggernade_q_spam", False)
        )
        ttk.Checkbutton(
            frame,
            text="Q spam between cycles (re-equip)",
            variable=self.triggernade_q_spam_var,
            command=self.save_settings,
        ).pack(anchor="w", padx=10, pady=2)

        # Triggernade Timings
        # Cook time - THE MOST IMPORTANT TIMING (use same layout as other sliders)
        cook_frame = ttk.Frame(frame)
        cook_frame.pack(fill="x", padx=10, pady=2)
        ttk.Label(
            cook_frame,
            text="Cook time:",
            width=20,
            anchor="w",
            font=("Arial", 9, "bold"),
        ).pack(side="left")
        self.trig_m1_hold_var = tk.IntVar(
            value=int(self.config.get("trig_m1_hold", 65))
        )

        def on_cook_slide(val):
            self.trig_m1_hold_var.set(int(float(val)))
            self.save_settings()

        cook_slider = ttk.Scale(
            cook_frame,
            from_=10,
            to=500,
            variable=self.trig_m1_hold_var,
            orient="horizontal",
            length=100,
            command=on_cook_slide,
        )
        cook_slider.pack(side="left", padx=5)

        cook_entry = tk.Entry(
            cook_frame,
            width=5,
            justify="center",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
        )
        cook_entry.pack(side="left")
        cook_entry.insert(0, str(self.trig_m1_hold_var.get()))

        def on_cook_entry(event=None):
            try:
                val = int(cook_entry.get())
                val = max(10, min(10000, val))
                self.trig_m1_hold_var.set(val)
                cook_entry.delete(0, "end")
                cook_entry.insert(0, str(val))
                self.save_settings()
            except ValueError:
                cook_entry.delete(0, "end")
                cook_entry.insert(0, str(self.trig_m1_hold_var.get()))

        def on_cook_var_change(*args):
            cook_entry.delete(0, "end")
            cook_entry.insert(0, str(self.trig_m1_hold_var.get()))

        cook_entry.bind("<Return>", on_cook_entry)
        cook_entry.bind("<FocusOut>", on_cook_entry)
        self.trig_m1_hold_var.trace_add("write", on_cook_var_change)
        ttk.Label(cook_frame, text="ms").pack(side="left")
        self.create_slider(frame, "M2 hold time:", "trig_m2_hold", 51, 10, 500, "ms")
        self.create_slider(frame, "Drag speed:", "trig_drag_speed", 8, 3, 20, "ms/step")
        self.create_slider(frame, "Delay before DC:", "trig_dc_delay", 10, 0, 200, "ms")
        self.create_slider(frame, "M1s while DC'd:", "trig_dc_throws", 10, 1, 30, "")
        self.create_slider(
            frame, "Time between M1s:", "trig_throw_delay", 100, 10, 500, "ms"
        )
        self.create_slider(
            frame, "Reconnect after M1 #:", "trig_reconnect_after", 1, 1, 20, ""
        )
        self.create_slider(
            frame, "Wait before E spam:", "wait_before_espam", 0, 0, 2000, "ms"
        )
        self.create_slider(
            frame, "E spam duration:", "espam_duration", 250, 0, 5000, "ms"
        )
        self.create_slider(
            frame, "M1s before E interweave:", "trig_m1_before_interweave", 1, 0, 20, ""
        )
        self.create_slider(
            frame, "Wait before next cycle:", "wait_before_cycle", 100, 0, 2000, "ms"
        )

        # Wolfpack loop settings header
        ttk.Label(
            frame, text="─ Wolfpack Loop Settings ─", font=("Arial", 9, "bold")
        ).pack(pady=(10, 5))
        self.create_slider(
            frame, "Loop M1 hold:", "wolfpack_m1_hold", 20, 10, 200, "ms"
        )
        self.create_slider(frame, "Loop M1 gap:", "wolfpack_m1_gap", 20, 10, 200, "ms")
        self.create_slider(
            frame, "Loop DC hold:", "wolfpack_dc_hold", 20, 10, 500, "ms"
        )
        self.create_slider(
            frame, "Loop DC gap:", "wolfpack_dc_gap", 600, 100, 3000, "ms"
        )

        trig_btn_frame = ttk.Frame(frame)
        trig_btn_frame.pack(pady=5)
        ttk.Button(
            trig_btn_frame,
            text="Reset Defaults",
            command=self.reset_triggernade_defaults,
        ).pack(side="left", padx=2)
        ttk.Button(
            trig_btn_frame, text="Export", width=7, command=self.export_triggernade
        ).pack(side="left", padx=2)
        ttk.Button(
            trig_btn_frame, text="Import", width=7, command=self.import_triggernade
        ).pack(side="left", padx=2)
        self.triggernade_status_var = tk.StringVar(value="Ready")
        self.triggernade_status_label = ttk.Label(
            frame, textvariable=self.triggernade_status_var, style="Dim.TLabel"
        )
        self.triggernade_status_label.pack(pady=5)

        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=10)

        # ===== THROW NO DC (EXPERIMENTAL) SECTION =====
        qd_header = ttk.Frame(frame)
        qd_header.pack(pady=(5, 5))
        ttk.Label(
            qd_header, text="── Throw NO DC (experimental) ──", style="Header.TLabel"
        ).pack(side="left")
        qd_info = ttk.Label(
            qd_header, text=" (?)", foreground=self.colors["text_dim"], cursor="hand2"
        )
        qd_info.pack(side="left")
        self._add_tooltip(
            qd_info,
            "Same as triggernade but NO DISCONNECT.\nUses right-click context menu drop instead of drag.\nRight-click on item → Left-click 'Drop to Ground'.\nSuper fast, almost instant.",
        )

        # Quick Drop Hotkey row
        qd_hk = ttk.Frame(frame)
        qd_hk.pack(fill="x", padx=10, pady=5)
        ttk.Label(qd_hk, text="Hotkey:").pack(side="left")
        self.quickdrop_hotkey_var = tk.StringVar(
            value=self.config.get("quickdrop_hotkey", "")
        )
        self.quickdrop_hotkey_entry = tk.Entry(
            qd_hk,
            textvariable=self.quickdrop_hotkey_var,
            width=15,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.quickdrop_hotkey_entry.pack(side="left", padx=5)
        self.quickdrop_record_btn = ttk.Button(
            qd_hk, text="Set", width=6, command=self.start_recording_quickdrop
        )
        self.quickdrop_record_btn.pack(side="left", padx=5)

        # Quick Drop position record
        qd_pos_frame = ttk.Frame(frame)
        qd_pos_frame.pack(fill="x", padx=10, pady=2)
        self.quickdrop_pos_btn = ttk.Button(
            qd_pos_frame,
            text="Record Pos",
            width=12,
            command=self.start_quickdrop_pos_recording,
        )
        self.quickdrop_pos_btn.pack(side="left")
        self.quickdrop_pos_var = tk.StringVar()
        # Load quick drop positions (right-click pos + left-click drop pos)
        qd_rclick = self.config.get("quickdrop_rclick_pos", [0, 0])
        qd_lclick = self.config.get("quickdrop_lclick_pos", [0, 0])
        self.quickdrop_rclick_pos = tuple(qd_rclick)
        self.quickdrop_lclick_pos = tuple(qd_lclick)
        self.quickdrop_pos_var.set(f"R:{qd_rclick} L:{qd_lclick}")
        ttk.Label(
            qd_pos_frame, textvariable=self.quickdrop_pos_var, font=("Consolas", 8)
        ).pack(side="left", padx=5)

        # Repeat checkbox
        self.quickdrop_repeat_var = tk.BooleanVar(
            value=self.config.get("quickdrop_repeat", False)
        )
        ttk.Checkbutton(
            frame,
            text="Auto (loop until pressed again)",
            variable=self.quickdrop_repeat_var,
            command=self.save_settings,
        ).pack(anchor="w", padx=10, pady=5)

        # Throw NO DC Timing Sliders (using create_slider for consistency)
        self.create_slider(frame, "Cook Time:", "quickdrop_cook", 1000, 100, 3000, "ms")
        self.create_slider(
            frame, "Inventory Delay:", "quickdrop_inv_delay", 50, 10, 500, "ms"
        )
        self.create_slider(
            frame, "Menu Delay:", "quickdrop_menu_delay", 20, 10, 200, "ms"
        )
        self.create_slider(
            frame, "Drop Delay:", "quickdrop_drop_delay", 20, 10, 200, "ms"
        )

        # Throw NO DC status
        self.quickdrop_status_var = tk.StringVar(value="Ready")
        self.quickdrop_status_label = ttk.Label(
            frame, textvariable=self.quickdrop_status_var, style="Dim.TLabel"
        )
        self.quickdrop_status_label.pack(pady=5)

        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=10)

        # ===== MINE DUPE SECTION =====
        mine_header = ttk.Frame(frame)
        mine_header.pack(pady=(5, 5))
        ttk.Label(mine_header, text="── Mine Dupe ──", style="Header.TLabel").pack(
            side="left"
        )
        mine_info = ttk.Label(
            mine_header, text=" (?)", foreground=self.colors["text_dim"], cursor="hand2"
        )
        mine_info.pack(side="left")
        self._add_tooltip(
            mine_info,
            "Record drag path from mine slot to ground.\nIf using SURVIVOR AUGMENT: record drag from UTILITY SLOT or it won't work.\n\nCOOK TIME: The use circle should be ALMOST full when inventory opens.\n- If mine deploys before/while opening inventory: reduce cook time\n- Make small adjustments until circle is mostly full on open\n\nDELAY BEFORE DC: Make very light adjustments if still not working.\n\nRECONNECT TO CLICK: If mine drops from inventory but duplicate doesn't place,\nadjust this timing in small increments either direction. Watch for consistency.\n\nTIP: Get it working SINGLE USE first. For auto-repeat, item must roll under your feet\nto be grabbed for looping. Drop piles of 1 of item you're duping around feet as backup copies to grab.",
        )

        # Mine Hotkey row
        mine_hk = ttk.Frame(frame)
        mine_hk.pack(fill="x", padx=10, pady=5)
        ttk.Label(mine_hk, text="Hotkey:").pack(side="left")
        self.mine_hotkey_var = tk.StringVar(value=self.config.get("mine_hotkey", ""))
        self.mine_hotkey_entry = tk.Entry(
            mine_hk,
            textvariable=self.mine_hotkey_var,
            width=15,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.mine_hotkey_entry.pack(side="left", padx=5)
        self.mine_record_btn = ttk.Button(
            mine_hk, text="Set", width=6, command=self.start_recording_mine
        )
        self.mine_record_btn.pack(side="left", padx=5)

        self.mine_repeat_var = tk.BooleanVar(
            value=self.config.get("mine_repeat", False)
        )
        ttk.Checkbutton(
            frame,
            text="Auto-repeat",
            variable=self.mine_repeat_var,
            command=self.save_settings,
        ).pack(anchor="w", padx=10, pady=2)

        # Mine drag/slot record
        mine_drag_frame = ttk.Frame(frame)
        mine_drag_frame.pack(fill="x", padx=10, pady=5)
        self.mine_drag_btn = ttk.Button(
            mine_drag_frame,
            text="Record",
            width=12,
            command=self.start_mine_drag_recording,
        )
        self.mine_drag_btn.pack(side="left")
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
        ttk.Label(
            mine_drag_frame, textvariable=self.mine_drag_var, font=("Consolas", 8)
        ).pack(side="left", padx=10)

        # Mine Timings
        ttk.Label(frame, text="Timings:", font=("Arial", 9, "bold")).pack(
            anchor="w", padx=10, pady=(5, 2)
        )

        # Cook time with extended range (slider 500, entry 10000)
        mine_cook_frame = ttk.Frame(frame)
        mine_cook_frame.pack(fill="x", padx=10, pady=2)
        ttk.Label(
            mine_cook_frame,
            text="Cook time:",
            width=20,
            anchor="w",
            font=("Arial", 9, "bold"),
        ).pack(side="left")
        self.mine_cook_var = tk.IntVar(value=int(self.config.get("mine_cook", 236)))

        def on_mine_cook_slide(val):
            self.mine_cook_var.set(int(float(val)))
            self.save_settings()

        mine_cook_slider = ttk.Scale(
            mine_cook_frame,
            from_=10,
            to=5000,
            variable=self.mine_cook_var,
            orient="horizontal",
            length=100,
            command=on_mine_cook_slide,
        )
        mine_cook_slider.pack(side="left", padx=5)

        mine_cook_entry = tk.Entry(
            mine_cook_frame,
            width=6,
            justify="center",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
        )
        mine_cook_entry.pack(side="left")
        mine_cook_entry.insert(0, str(self.mine_cook_var.get()))

        def on_mine_cook_entry(event=None):
            try:
                val = int(mine_cook_entry.get())
                val = max(10, min(10000, val))
                self.mine_cook_var.set(val)
                mine_cook_entry.delete(0, "end")
                mine_cook_entry.insert(0, str(val))
                self.save_settings()
            except ValueError:
                mine_cook_entry.delete(0, "end")
                mine_cook_entry.insert(0, str(self.mine_cook_var.get()))

        def on_mine_cook_var_change(*args):
            mine_cook_entry.delete(0, "end")
            mine_cook_entry.insert(0, str(self.mine_cook_var.get()))

        mine_cook_entry.bind("<Return>", on_mine_cook_entry)
        mine_cook_entry.bind("<FocusOut>", on_mine_cook_entry)
        self.mine_cook_var.trace_add("write", on_mine_cook_var_change)
        ttk.Label(mine_cook_frame, text="ms").pack(side="left")

        # Defaults based on YOUR successful recordings
        self.create_slider(
            frame, "Delay before DC:", "mine_dc_delay", 99, 0, 500, "ms", bold=True
        )
        self.create_slider(frame, "Drag speed:", "mine_drag_speed", 8, 3, 20, "ms/step")
        self.create_slider(
            frame, "Pre-close delay:", "mine_pre_close", 100, 0, 2000, "ms"
        )
        self.create_slider(
            frame, "TAB hold (close):", "mine_tab_hold", 80, 20, 300, "ms"
        )
        self.create_slider(
            frame,
            "Close to reconnect:",
            "mine_close_reconnect",
            409,
            100,
            2000,
            "ms",
            bold=True,
        )
        self.create_slider(
            frame, "Reconnect to click:", "mine_click_delay", 7, 0, 500, "ms", bold=True
        )
        self.create_slider(
            frame,
            "Dupe click hold:",
            "mine_pickup_hold",
            1336,
            100,
            3000,
            "ms",
            bold=True,
        )
        self.create_slider(frame, "Delay before E:", "mine_e_delay", 868, 0, 2000, "ms")
        self.create_slider(
            frame, "Delay before loop:", "mine_loop_delay", 550, 0, 2000, "ms"
        )

        # Q reselect option
        reselect_frame = ttk.Frame(frame)
        reselect_frame.pack(fill="x", padx=10, pady=5)
        self.mine_reselect_var = tk.BooleanVar(
            value=self.config.get("mine_reselect", True)
        )
        ttk.Checkbutton(
            reselect_frame,
            text="Q to reselect",
            variable=self.mine_reselect_var,
            command=self.save_settings,
        ).pack(side="left")

        # Q mode: simple tap or recorded radial
        default_q_recording = [
            [1920, 1080],
            [1920, 1064],
            [1920, 1046],
            [1920, 1020],
            [1920, 982],
            [1920, 949],
            [1922, 914],
            [1925, 884],
            [1928, 852],
            [1922, 1058],
            [1926, 1035],
            [1927, 1012],
            [1930, 993],
            [1922, 1065],
            [1924, 1049],
        ]
        self.mine_q_mode_var = tk.StringVar(
            value=self.config.get("mine_q_mode", "radial")
        )
        ttk.Radiobutton(
            reselect_frame,
            text="Simple tap",
            variable=self.mine_q_mode_var,
            value="simple",
            command=self.save_settings,
        ).pack(side="left", padx=(10, 5))
        ttk.Radiobutton(
            reselect_frame,
            text="Radial:",
            variable=self.mine_q_mode_var,
            value="radial",
            command=self.save_settings,
        ).pack(side="left")

        # Direction picker button - opens compass popup
        self.mine_q_direction_var = tk.StringVar(
            value=self.config.get("mine_q_direction", "S")
        )
        self.mine_q_dir_btn = ttk.Button(
            reselect_frame,
            text=self.mine_q_direction_var.get(),
            width=3,
            command=self._show_direction_picker,
        )
        self.mine_q_dir_btn.pack(side="left", padx=2)

        # Mouse nudge option (move mouse between loops)
        nudge_frame = ttk.Frame(frame)
        nudge_frame.pack(fill="x", padx=10, pady=5)
        self.mine_nudge_var = tk.BooleanVar(value=self.config.get("mine_nudge", True))
        ttk.Checkbutton(
            nudge_frame,
            text="Nudge mouse",
            variable=self.mine_nudge_var,
            command=self.save_settings,
        ).pack(side="left")
        self.mine_nudge_px_var = tk.IntVar(value=self.config.get("mine_nudge_px", 50))
        nudge_entry = tk.Entry(
            nudge_frame,
            textvariable=self.mine_nudge_px_var,
            width=5,
            justify="center",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
        )
        nudge_entry.pack(side="left", padx=5)
        nudge_entry.bind("<Return>", lambda e: self.save_settings())
        nudge_entry.bind("<FocusOut>", lambda e: self.save_settings())
        ttk.Label(nudge_frame, text="px right per loop").pack(side="left")

        mine_btn_frame = ttk.Frame(frame)
        mine_btn_frame.pack(pady=5)
        ttk.Button(
            mine_btn_frame, text="Reset Defaults", command=self.reset_mine_defaults
        ).pack(side="left", padx=2)
        ttk.Button(
            mine_btn_frame, text="Export", width=7, command=self.export_mine
        ).pack(side="left", padx=2)
        ttk.Button(
            mine_btn_frame, text="Import", width=7, command=self.import_mine
        ).pack(side="left", padx=2)
        self.mine_status_var = tk.StringVar(value="Ready")
        self.mine_status_label = ttk.Label(
            frame, textvariable=self.mine_status_var, style="Dim.TLabel"
        )
        self.mine_status_label.pack(pady=5)

        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=10)

        # ===== CUSTOM MACROS SECTION =====
        custom_macro_header = ttk.Frame(frame)
        custom_macro_header.pack(pady=(5, 5))
        ttk.Label(
            custom_macro_header, text="── Custom Macros ──", style="Header.TLabel"
        ).pack(side="left")
        custom_macro_info = ttk.Label(
            custom_macro_header,
            text=" (?)",
            foreground=self.colors["text_dim"],
            cursor="hand2",
        )
        custom_macro_info.pack(side="left")
        self._add_tooltip(
            custom_macro_info,
            "Record and playback custom macros.\nCtrl+Enter to start/stop recording.\nCan record any key including ESC.",
        )

        # Tab buttons container
        self.macro_tabs_container = ttk.Frame(frame)
        self.macro_tabs_container.pack(fill="x", padx=10, pady=5)

        # Left scroll button (hidden by default)
        self.macro_scroll_left = tk.Button(
            self.macro_tabs_container,
            text="◀",
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            bd=0,
            font=("Arial", 8),
            padx=4,
            pady=2,
            command=lambda: self._scroll_macro_tabs(-1),
        )

        # Canvas for scrollable tabs
        self.macro_tabs_canvas = tk.Canvas(
            self.macro_tabs_container,
            height=24,
            highlightthickness=0,
            bg=self.colors["bg"],
        )
        self.macro_tabs_canvas.pack(side="left", fill="x", expand=True)

        # Right scroll button (hidden by default)
        self.macro_scroll_right = tk.Button(
            self.macro_tabs_container,
            text="▶",
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            bd=0,
            font=("Arial", 8),
            padx=4,
            pady=2,
            command=lambda: self._scroll_macro_tabs(1),
        )

        # Add button (always visible)
        self.macro_add_btn = tk.Button(
            self.macro_tabs_container,
            text="+",
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            bd=0,
            font=("Arial", 9),
            padx=6,
            pady=2,
            command=self._add_new_macro,
        )
        self.macro_add_btn.pack(side="left", padx=2)

        # Frame inside canvas for tab buttons
        self.macro_tabs_frame = ttk.Frame(self.macro_tabs_canvas)
        self.macro_tabs_window = self.macro_tabs_canvas.create_window(
            (0, 0), window=self.macro_tabs_frame, anchor="nw"
        )

        # Configure scrolling
        self.macro_tabs_frame.bind("<Configure>", self._update_macro_tabs_scroll)
        self.macro_tabs_canvas.bind(
            "<MouseWheel>", lambda e: self._scroll_macro_tabs(-1 if e.delta > 0 else 1)
        )

        self.macro_tab_buttons = []
        self._build_macro_tabs()

        # Macro content frame (holds name, hotkey, speed, buttons)
        self.macro_content_frame = ttk.Frame(frame)
        self.macro_content_frame.pack(fill="x", padx=10)

        # Name row
        name_frame = ttk.Frame(self.macro_content_frame)
        name_frame.pack(fill="x", pady=2)
        ttk.Label(name_frame, text="Name:").pack(side="left")
        self.macro_name_var = tk.StringVar()
        self.macro_name_entry = tk.Entry(
            name_frame,
            textvariable=self.macro_name_var,
            width=20,
            bd=0,
            highlightthickness=1,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            highlightbackground=self.colors.get("bg_lighter", "#555555"),
        )
        self.macro_name_entry.pack(side="left", padx=5)
        self.macro_name_entry.bind("<Return>", lambda e: self._on_macro_name_change())
        self.macro_name_entry.bind("<FocusOut>", lambda e: self._on_macro_name_change())

        # Hotkey row
        hotkey_frame = ttk.Frame(self.macro_content_frame)
        hotkey_frame.pack(fill="x", pady=2)
        ttk.Label(hotkey_frame, text="Hotkey:").pack(side="left")
        self.macro_hotkey_var = tk.StringVar()
        self.macro_hotkey_entry = tk.Entry(
            hotkey_frame,
            textvariable=self.macro_hotkey_var,
            width=15,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.macro_hotkey_entry.pack(side="left", padx=5)
        self.macro_hk_btn = ttk.Button(
            hotkey_frame,
            text="Set",
            width=6,
            command=self._start_recording_macro_hotkey,
        )
        self.macro_hk_btn.pack(side="left", padx=5)

        # Speed slider row
        speed_frame = ttk.Frame(self.macro_content_frame)
        speed_frame.pack(fill="x", pady=2)
        ttk.Label(speed_frame, text="Speed:").pack(side="left")
        self.macro_speed_var = tk.DoubleVar(value=1.0)
        self.macro_speed_slider = ttk.Scale(
            speed_frame,
            from_=0.1,
            to=5.0,
            variable=self.macro_speed_var,
            orient="horizontal",
            length=120,
            command=self._on_macro_speed_change,
        )
        self.macro_speed_slider.pack(side="left", padx=5)
        self.macro_speed_label = ttk.Label(speed_frame, text="1.0x", width=5)
        self.macro_speed_label.pack(side="left")

        # Keep Timing checkbox
        self.macro_keep_timing_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            speed_frame,
            text="Keep Timing",
            variable=self.macro_keep_timing_var,
            command=self._on_macro_keep_timing_change,
        ).pack(side="left", padx=10)

        # Repeat options row
        repeat_frame = ttk.Frame(self.macro_content_frame)
        repeat_frame.pack(fill="x", pady=2)

        self.macro_repeat_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            repeat_frame,
            text="Repeat",
            variable=self.macro_repeat_var,
            command=self._on_macro_repeat_change,
        ).pack(side="left")

        self.macro_repeat_times_var = tk.StringVar(value="1")
        self.macro_repeat_times_entry = tk.Entry(
            repeat_frame,
            textvariable=self.macro_repeat_times_var,
            width=4,
            bd=0,
            highlightthickness=1,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            justify="center",
        )
        self.macro_repeat_times_entry.pack(side="left", padx=2)
        # Only allow integers
        self.macro_repeat_times_entry.bind("<KeyRelease>", self._validate_repeat_times)
        ttk.Label(repeat_frame, text="times").pack(side="left")

        self.macro_repeat_infinite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            repeat_frame,
            text="∞",
            variable=self.macro_repeat_infinite_var,
            command=self._on_macro_infinite_change,
        ).pack(side="left", padx=5)

        ttk.Label(repeat_frame, text="Delay:").pack(side="left", padx=(10, 0))
        self.macro_repeat_delay_var = tk.StringVar(value="0")
        self.macro_repeat_delay_entry = tk.Entry(
            repeat_frame,
            textvariable=self.macro_repeat_delay_var,
            width=4,
            bd=0,
            highlightthickness=1,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            justify="center",
        )
        self.macro_repeat_delay_entry.pack(side="left", padx=2)
        self.macro_repeat_delay_entry.bind("<KeyRelease>", self._validate_repeat_delay)
        ttk.Label(repeat_frame, text="s").pack(side="left")

        # Buttons row
        macro_btn_frame = ttk.Frame(self.macro_content_frame)
        macro_btn_frame.pack(pady=2)
        self.macro_record_btn = ttk.Button(
            macro_btn_frame,
            text="Record",
            width=8,
            command=self.start_custom_macro_recording,
        )
        self.macro_record_btn.pack(side="left", padx=2)
        self.macro_play_btn = ttk.Button(
            macro_btn_frame, text="Play", width=8, command=self._toggle_macro_play
        )
        self.macro_play_btn.pack(side="left", padx=2)
        self.macro_delete_btn = ttk.Button(
            macro_btn_frame, text="Delete", width=6, command=self._delete_current_macro
        )
        self.macro_delete_btn.pack(side="left", padx=2)

        # Export/Import row
        macro_io_frame = ttk.Frame(self.macro_content_frame)
        macro_io_frame.pack(pady=2)
        ttk.Button(
            macro_io_frame, text="Export", width=8, command=self._export_current_macro
        ).pack(side="left", padx=2)
        ttk.Button(
            macro_io_frame, text="Import", width=8, command=self._import_macro
        ).pack(side="left", padx=2)

        # Status label
        self.macro_status_var = tk.StringVar(value="Ctrl+Enter to record")
        self.macro_status_label = ttk.Label(
            frame, textvariable=self.macro_status_var, style="Dim.TLabel"
        )
        self.macro_status_label.pack(pady=(5, 10))

        # Load current macro data into UI
        self._load_current_macro_to_ui()

        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=10)

        # ===== E-SPAM COLLECTION SECTION =====
        espam_header = ttk.Frame(frame)
        espam_header.pack(pady=(5, 5))
        ttk.Label(
            espam_header, text="── E-Spam Collection ──", style="Header.TLabel"
        ).pack(side="left")
        espam_info = ttk.Label(
            espam_header,
            text=" (?)",
            foreground=self.colors["text_dim"],
            cursor="hand2",
        )
        espam_info.pack(side="left")
        self._add_tooltip(
            espam_info, "Used to gather already completed mines/triggernades."
        )

        espam_hk = ttk.Frame(frame)
        espam_hk.pack(fill="x", padx=10, pady=5)
        ttk.Label(espam_hk, text="Hotkey:").pack(side="left")
        self.espam_hotkey_var = tk.StringVar(value=self.config.get("espam_hotkey", ""))
        self.espam_hotkey_entry = tk.Entry(
            espam_hk,
            textvariable=self.espam_hotkey_var,
            width=15,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.espam_hotkey_entry.pack(side="left", padx=5)
        self.espam_record_btn = ttk.Button(
            espam_hk, text="Set", width=6, command=self.start_recording_espam
        )
        self.espam_record_btn.pack(side="left", padx=5)

        # Hold vs Toggle option
        self.espam_hold_mode_var = tk.BooleanVar(
            value=self.config.get("espam_hold_mode", False)
        )
        ttk.Checkbutton(
            frame,
            text="Hold to activate (vs toggle)",
            variable=self.espam_hold_mode_var,
            command=self.save_settings,
        ).pack(anchor="w", padx=10, pady=2)

        # Time between E spam bursts (in ms)
        self.create_slider(
            frame, "Time before repeat:", "espam_repeat_delay", 0, 0, 5000, "ms"
        )

        self.espam_status_var = tk.StringVar(value="Ready")
        self.espam_status_label = ttk.Label(
            frame, textvariable=self.espam_status_var, style="Dim.TLabel"
        )
        self.espam_status_label.pack(pady=5)

        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=10)

        # ===== E-DROP COLLECTION SECTION =====
        edrop_header = ttk.Frame(frame)
        edrop_header.pack(pady=(5, 5))
        ttk.Label(
            edrop_header, text="── E-Drop Collection ──", style="Header.TLabel"
        ).pack(side="left")
        edrop_info = ttk.Label(
            edrop_header,
            text=" (?)",
            foreground=self.colors["text_dim"],
            cursor="hand2",
        )
        edrop_info.pack(side="left")
        self._add_tooltip(
            edrop_info,
            "Disconnect → Press E → Right-click item → Drop → Reconnect\n\nUseful for collecting items with disconnect protection.",
        )

        # E-Drop Hotkey
        edrop_hk = ttk.Frame(frame)
        edrop_hk.pack(fill="x", padx=10, pady=5)
        ttk.Label(edrop_hk, text="Hotkey:").pack(side="left")
        self.edrop_hotkey_var = tk.StringVar(value=self.config.get("edrop_hotkey", ""))
        self.edrop_hotkey_entry = tk.Entry(
            edrop_hk,
            textvariable=self.edrop_hotkey_var,
            width=15,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.edrop_hotkey_entry.pack(side="left", padx=5)
        self.edrop_record_btn = ttk.Button(
            edrop_hk, text="Set", width=6, command=self.start_recording_edrop
        )
        self.edrop_record_btn.pack(side="left", padx=5)

        # E-Drop Position Recording
        edrop_pos_frame = ttk.Frame(frame)
        edrop_pos_frame.pack(fill="x", padx=10, pady=2)
        self.edrop_pos_btn = ttk.Button(
            edrop_pos_frame,
            text="Record Positions",
            width=16,
            command=self.start_edrop_pos_recording,
        )
        self.edrop_pos_btn.pack(side="left")
        self.edrop_pos_var = tk.StringVar()
        # Load positions
        edrop_rclick = self.config.get("edrop_rclick_pos", [0, 0])
        edrop_drop = self.config.get("edrop_drop_pos", [0, 0])
        self.edrop_rclick_pos = tuple(edrop_rclick)
        self.edrop_drop_pos = tuple(edrop_drop)
        self.edrop_pos_var.set(f"RClick:{edrop_rclick} Drop:{edrop_drop}")
        ttk.Label(
            edrop_pos_frame, textvariable=self.edrop_pos_var, font=("Consolas", 8)
        ).pack(side="left", padx=5)

        # Repeat checkbox
        self.edrop_repeat_var = tk.BooleanVar(
            value=self.config.get("edrop_repeat", False)
        )
        ttk.Checkbutton(
            frame,
            text="Auto (loop until pressed again)",
            variable=self.edrop_repeat_var,
            command=self.save_settings,
        ).pack(anchor="w", padx=10, pady=5)

        # E-Drop Timings
        self.create_slider(
            frame, "Wait before E:", "edrop_wait_before_e", 200, 0, 1000, "ms"
        )
        self.create_slider(
            frame, "E press duration:", "edrop_e_duration", 50, 10, 200, "ms"
        )
        self.create_slider(
            frame, "Wait before inventory:", "edrop_wait_before_inv", 100, 0, 500, "ms"
        )
        self.create_slider(
            frame, "Inventory delay:", "edrop_inv_delay", 150, 50, 500, "ms"
        )
        self.create_slider(
            frame, "Right-click delay:", "edrop_rclick_delay", 100, 20, 300, "ms"
        )
        self.create_slider(
            frame, "Drop menu delay:", "edrop_drop_delay", 100, 20, 300, "ms"
        )
        self.create_slider(
            frame, "Wait after reconnect:", "edrop_reconnect_delay", 200, 50, 1000, "ms"
        )
        self.create_slider(frame, "Loop delay:", "edrop_loop_delay", 500, 0, 2000, "ms")

        ttk.Button(
            frame, text="Reset E-Drop Defaults", command=self.reset_edrop_defaults
        ).pack(pady=5)
        self.edrop_status_var = tk.StringVar(value="Ready")
        self.edrop_status_label = ttk.Label(
            frame, textvariable=self.edrop_status_var, style="Dim.TLabel"
        )
        self.edrop_status_label.pack(pady=5)

        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=10)

        # ===== HOTKEYS (Minimize) =====
        ttk.Label(frame, text="── Window Hotkeys ──", style="Header.TLabel").pack(
            pady=(5, 5)
        )

        # Minimize hotkey
        min_hk_frame = ttk.Frame(frame)
        min_hk_frame.pack(fill="x", padx=10, pady=2)
        ttk.Label(min_hk_frame, text="Minimize:").pack(side="left")
        self.minimize_hotkey_var = tk.StringVar(
            value=self.config.get("minimize_hotkey", "")
        )
        self.minimize_hotkey_entry = tk.Entry(
            min_hk_frame,
            textvariable=self.minimize_hotkey_var,
            width=10,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.minimize_hotkey_entry.pack(side="left", padx=5)
        self.minimize_record_btn = ttk.Button(
            min_hk_frame, text="Set", width=4, command=self.start_recording_minimize
        )
        self.minimize_record_btn.pack(side="left")
        self.recording_minimize = False

        # Minimize to tray hotkey
        tray_hk_frame = ttk.Frame(frame)
        tray_hk_frame.pack(fill="x", padx=10, pady=2)
        ttk.Label(tray_hk_frame, text="Minimize to Tray:").pack(side="left")
        self.tray_hotkey_var = tk.StringVar(value=self.config.get("tray_hotkey", ""))
        self.tray_hotkey_entry = tk.Entry(
            tray_hk_frame,
            textvariable=self.tray_hotkey_var,
            width=10,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.tray_hotkey_entry.pack(side="left", padx=5)
        self.tray_record_btn = ttk.Button(
            tray_hk_frame, text="Set", width=4, command=self.start_recording_tray
        )
        self.tray_record_btn.pack(side="left")
        self.recording_tray = False

        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=10)

        # ===== APPEARANCE SETTINGS =====
        ttk.Label(frame, text="── Appearance ──", style="Header.TLabel").pack(
            pady=(5, 5)
        )

        # Color pickers in a row
        colors_frame = ttk.Frame(frame)
        colors_frame.pack(fill="x", padx=10, pady=5)

        # Background color
        ttk.Label(colors_frame, text="BG:").pack(side="left")
        self.bg_color_var = tk.StringVar(value=self.config.get("bg_color", "#1e1e1e"))
        self.bg_color_btn = tk.Button(
            colors_frame,
            text="",
            width=3,
            height=1,
            bg=self.bg_color_var.get(),
            relief="solid",
            bd=1,
            cursor="hand2",
            command=self._pick_bg_color,
        )
        self.bg_color_btn.pack(side="left", padx=(2, 10))

        # Text color
        ttk.Label(colors_frame, text="Text:").pack(side="left")
        self.fg_color_var = tk.StringVar(value=self.config.get("fg_color", "#e0e0e0"))
        self.fg_color_btn = tk.Button(
            colors_frame,
            text="",
            width=3,
            height=1,
            bg=self.fg_color_var.get(),
            relief="solid",
            bd=1,
            cursor="hand2",
            command=self._pick_fg_color,
        )
        self.fg_color_btn.pack(side="left", padx=(2, 10))

        # Accent color
        ttk.Label(colors_frame, text="Accent:").pack(side="left")
        self.accent_color_var = tk.StringVar(
            value=self.config.get("accent_color", "#e94560")
        )
        self.accent_color_btn = tk.Button(
            colors_frame,
            text="",
            width=3,
            height=1,
            bg=self.accent_color_var.get(),
            relief="solid",
            bd=1,
            cursor="hand2",
            command=self._pick_accent_color,
        )
        self.accent_color_btn.pack(side="left", padx=2)

        # Transparency slider
        trans_frame = ttk.Frame(frame)
        trans_frame.pack(fill="x", padx=10, pady=2)
        ttk.Label(trans_frame, text="Transparency:").pack(side="left")
        loaded_trans = self.config.get("transparency", 100)
        self.transparency_var = tk.IntVar(value=loaded_trans)
        trans_slider = ttk.Scale(
            trans_frame,
            from_=50,
            to=100,
            variable=self.transparency_var,
            orient="horizontal",
            length=100,
            command=self._on_transparency_change,
        )
        trans_slider.pack(side="left", padx=5)
        self.trans_label = ttk.Label(trans_frame, text=f"{loaded_trans}%")
        self.trans_label.pack(side="left")

        # Apply initial transparency
        self._apply_transparency()

        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10, pady=10)

        # ===== GLOBAL EXPORT/IMPORT =====
        ttk.Label(frame, text="── All Settings ──", style="Header.TLabel").pack(
            pady=(5, 5)
        )
        global_btn_frame = ttk.Frame(frame)
        global_btn_frame.pack(pady=5)
        ttk.Button(
            global_btn_frame,
            text="Export All",
            width=10,
            command=self.export_all_settings,
        ).pack(side="left", padx=2)
        ttk.Button(
            global_btn_frame,
            text="Import All",
            width=10,
            command=self.import_all_settings,
        ).pack(side="left", padx=2)

        # ===== RESET ALL =====
        ttk.Button(
            frame, text="Reset ALL Settings", command=self.reset_all_settings
        ).pack(pady=5)

        # ===== STOP ALL HOTKEY =====
        stop_frame = ttk.Frame(frame)
        stop_frame.pack(fill="x", padx=10, pady=(15, 5))
        ttk.Label(stop_frame, text="Stop All:").pack(side="left")
        self.stop_hotkey_var = tk.StringVar(value=self.config.get("stop_hotkey", "esc"))
        self.stop_hotkey_entry = tk.Entry(
            stop_frame,
            textvariable=self.stop_hotkey_var,
            width=15,
            state="readonly",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            readonlybackground=self.colors["bg_light"],
        )
        self.stop_hotkey_entry.pack(side="left", padx=5)
        self.stop_record_btn = ttk.Button(
            stop_frame, text="Set", width=6, command=self.start_recording_stop
        )
        self.stop_record_btn.pack(side="left", padx=5)

        # ===== RESIZE GRIP (bottom of window) =====
        resize_grip = tk.Frame(
            self.root, bg=self.colors["bg_light"], height=8, cursor="sb_v_double_arrow"
        )
        resize_grip.pack(side="bottom", fill="x")

        def start_resize(event):
            self._resize_start_y = event.y_root
            self._resize_start_height = self.root.winfo_height()

        def do_resize(event):
            delta = event.y_root - self._resize_start_y
            new_height = max(400, self._resize_start_height + delta)  # Min height 400
            self.root.geometry(f"442x{new_height}")

        resize_grip.bind("<Button-1>", start_resize)
        resize_grip.bind("<B1-Motion>", do_resize)

    def create_slider(
        self,
        parent,
        label,
        config_key,
        default,
        min_val,
        max_val,
        unit,
        bold=False,
        tooltip=None,
    ):
        """Create a slider row with label, slider, and editable value entry"""
        row = ttk.Frame(parent)
        row.pack(fill="x", padx=10, pady=2)

        if bold:
            lbl = ttk.Label(
                row, text=label, width=20, anchor="w", font=("Segoe UI", 9, "bold")
            )
        else:
            lbl = ttk.Label(row, text=label, width=20, anchor="w")
        lbl.pack(side="left")

        # Add tooltip if provided
        if tooltip:

            def show_tooltip(event):
                tip = tk.Toplevel(row)
                tip.wm_overrideredirect(True)
                tip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                tip_label = tk.Label(
                    tip,
                    text=tooltip,
                    justify="left",
                    background="#ffffe0",
                    relief="solid",
                    borderwidth=1,
                    font=("Segoe UI", 8),
                    wraplength=300,
                )
                tip_label.pack()
                row._tooltip = tip

            def hide_tooltip(event):
                if hasattr(row, "_tooltip"):
                    row._tooltip.destroy()
                    del row._tooltip

            lbl.bind("<Enter>", show_tooltip)
            lbl.bind("<Leave>", hide_tooltip)

        var = tk.IntVar(value=int(self.config.get(config_key, default)))
        setattr(self, f"{config_key}_var", var)

        def on_slide(val):
            var.set(int(float(val)))
            self.save_settings()

        slider = ttk.Scale(
            row,
            from_=min_val,
            to=max_val,
            variable=var,
            orient="horizontal",
            length=100,
            command=on_slide,
        )
        slider.pack(side="left", padx=5)

        # Editable entry instead of label (no border)
        entry = tk.Entry(
            row,
            width=5,
            justify="center",
            bd=0,
            highlightthickness=0,
            bg=self.colors["bg_light"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
        )
        entry.pack(side="left")
        entry.insert(0, str(var.get()))

        def on_entry_change(event=None):
            try:
                val = int(entry.get())
                var.set(val)  # No clamping - accept any value
                self.save_settings()
            except ValueError:
                entry.delete(0, "end")
                entry.insert(0, str(var.get()))

        def on_var_change(*args):
            entry.delete(0, "end")
            entry.insert(0, str(var.get()))

        entry.bind("<Return>", on_entry_change)
        entry.bind("<FocusOut>", on_entry_change)
        var.trace_add("write", on_var_change)

        if unit:
            ttk.Label(row, text=unit).pack(side="left")

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
        overlay.configure(bg="black")
        overlay.attributes("-alpha", 0.7)  # Semi-transparent
        overlay.geometry(
            f"{self.root.winfo_width()}x{self.root.winfo_height()}+{self.root.winfo_x()}+{self.root.winfo_y()}"
        )

        # Create popup for direction picker
        popup = tk.Toplevel(self.root)
        popup.title("Select Direction")
        popup.overrideredirect(True)
        popup.configure(bg="black")
        popup.attributes("-transparentcolor", "black")  # Make black corners transparent
        popup.attributes("-topmost", True)

        # Load direction images (handle PyInstaller bundle)
        if getattr(sys, "frozen", False):
            script_dir = sys._MEIPASS
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))

        img_files = {
            "NONE": "NONE.png",
            "N": "N.png",
            "NE": "NE.png",
            "E": "E.png",
            "SE": "SE.png",
            "S": "S.png",
            "SW": "SW.png",
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
        title_label = tk.Label(
            popup,
            text="Select Slot",
            bg="white",
            fg="black",
            font=("Arial", 12, "bold"),
            padx=10,
            pady=5,
        )
        title_label.pack(pady=(5, 10))

        # Create canvas
        canvas = tk.Canvas(
            popup, width=img_width, height=img_height, bg="black", highlightthickness=0
        )
        canvas.pack()
        canvas.create_image(0, 0, anchor="nw", image=images["NONE"], tags="radial")
        # White circle border (3px)
        canvas.create_oval(
            1, 1, img_width - 1, img_height - 1, outline="white", width=3, tags="border"
        )
        # Show current selection in center (3px up from center)
        selected = self.mine_q_direction_var.get()
        canvas.create_text(
            center_x - 3,
            center_y - 3,
            text=selected,
            fill="black",
            font=("Arial", 10, "bold"),
            tags="dirtext",
        )

        # Store reference to prevent garbage collection
        popup.images = images
        current_dir = [None]

        def angle_to_direction(angle):
            """Convert angle (degrees, 0=right, counter-clockwise) to direction"""
            # Calibrated: N=67-113, NE=22-70, E=wraps 0, SE=290-338, S=247-295, SW=206-253
            # Ring: inner=92, outer=151
            angle = angle % 360
            if 68 <= angle < 113:  # N
                return "N"
            elif 22 <= angle < 68:  # NE
                return "NE"
            elif angle < 22 or angle >= 338:  # E (wraps around 0)
                return "E"
            elif 292 <= angle < 338:  # SE
                return "SE"
            elif 250 <= angle < 292:  # S
                return "S"
            elif 206 <= angle < 250:  # SW
                return "SW"
            # 113-206 is NW/W territory - not selectable
            return None

        def on_mouse_move(event):
            dx = event.x - center_x
            dy = center_y - event.y  # Flip Y for standard math coords
            dist = math.sqrt(dx * dx + dy * dy)

            # Only detect in the ring area (not too close to center, not outside)
            if dist < 101 or dist > 166:  # Scaled 10% (92*1.1, 151*1.1)
                new_dir = None
            else:
                angle = math.degrees(math.atan2(dy, dx))
                if angle < 0:
                    angle += 360
                new_dir = angle_to_direction(angle)

            if new_dir != current_dir[0]:
                current_dir[0] = new_dir  # type: ignore[assignment]
                img_key = new_dir if new_dir and new_dir in images else "NONE"
                canvas.delete("radial")
                canvas.create_image(
                    0, 0, anchor="nw", image=images[img_key], tags="radial"
                )
                # Redraw border on top
                canvas.delete("border")
                canvas.create_oval(
                    1,
                    1,
                    img_width - 1,
                    img_height - 1,
                    outline="white",
                    width=3,
                    tags="border",
                )
                # Update center text
                canvas.delete("dirtext")
                display_text = new_dir if new_dir else self.mine_q_direction_var.get()
                canvas.create_text(
                    center_x - 3,
                    center_y - 3,
                    text=display_text,
                    fill="black",
                    font=("Arial", 10, "bold"),
                    tags="dirtext",
                )

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
                canvas.create_image(
                    0, 0, anchor="nw", image=images["NONE"], tags="radial"
                )
                canvas.delete("border")
                canvas.create_oval(
                    1,
                    1,
                    img_width - 1,
                    img_height - 1,
                    outline="white",
                    width=3,
                    tags="border",
                )
                canvas.delete("dirtext")
                canvas.create_text(
                    center_x - 3,
                    center_y - 3,
                    text=self.mine_q_direction_var.get(),
                    fill="black",
                    font=("Arial", 10, "bold"),
                    tags="dirtext",
                )

        canvas.bind("<Motion>", on_mouse_move)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)
        popup.bind("<Button-1>", on_click)  # Click anywhere on popup closes
        overlay.bind("<Button-1>", lambda e: close_picker())  # Click overlay closes
        popup.bind("<Escape>", lambda e: close_picker())

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
            "N": (0, -dist),
            "NE": (dist, -dist),
            "E": (dist, 0),
            "SE": (dist, dist),
            "S": (0, dist),
            "SW": (-dist, dist),
        }

        direction = self.mine_q_direction_var.get()
        dx, dy = direction_deltas.get(direction, (0, dist))  # Default to South

        print(f"[Q RADIAL] Direction: {direction}, delta: ({dx}, {dy})")

        # Press Q and wait for radial to open
        pynput_keyboard.press("q")
        time.sleep(0.3)

        # Move in steps for natural feel
        steps = 10
        for i in range(steps):
            pynput_mouse.move(dx // steps, dy // steps)
            time.sleep(0.015)

        time.sleep(0.1)
        pynput_keyboard.release("q")
        print(f"[Q RADIAL] Done - selected {direction}")

    # ===== CUSTOM MACROS METHODS =====

    def _build_macro_tabs(self):
        """Build the tab buttons for custom macros"""
        # Clear existing buttons
        for widget in self.macro_tabs_frame.winfo_children():
            widget.destroy()
        self.macro_tab_buttons = []

        bg = self.colors["bg"]
        bg_light = self.colors["bg_light"]
        bg_lighter = self.colors.get("bg_lighter", self._adjust_color(bg, 45))
        text = self.colors["text"]
        highlight = self.colors["highlight"]

        # Update canvas and scroll buttons colors
        if hasattr(self, "macro_tabs_canvas"):
            self.macro_tabs_canvas.config(bg=bg)
        if hasattr(self, "macro_scroll_left"):
            self.macro_scroll_left.config(bg=bg_light, fg=text)
            self.macro_scroll_right.config(bg=bg_light, fg=text)
            self.macro_add_btn.config(bg=bg_light, fg=text)

        macros = self.custom_macros_data.get("macros", [])
        for i, macro in enumerate(macros):
            is_active = i == self.active_macro_index
            name = macro.get("name", f"M{i+1}")
            if is_active:
                btn = tk.Button(
                    self.macro_tabs_frame,
                    text=name,
                    bg=bg_lighter,
                    fg=text,
                    activebackground=highlight,
                    activeforeground="white",
                    bd=0,
                    relief="flat",
                    cursor="hand2",
                    padx=6,
                    pady=2,
                    font=("Arial", 9),
                    command=lambda idx=i: self._on_macro_tab_click(idx),
                )
            else:
                btn = tk.Button(
                    self.macro_tabs_frame,
                    text=name,
                    bg=bg_light,
                    fg=text,
                    activebackground=bg_lighter,
                    activeforeground=text,
                    bd=0,
                    relief="flat",
                    cursor="hand2",
                    padx=6,
                    pady=2,
                    font=("Arial", 9),
                    command=lambda idx=i: self._on_macro_tab_click(idx),
                )
            btn.pack(side="left", padx=1)
            self.macro_tab_buttons.append(btn)

        self._update_macro_tabs_scroll()
        self._update_macro_entry_colors()

    def _update_macro_tabs_scroll(self, event=None):
        """Update scroll region and show/hide scroll buttons"""
        self.macro_tabs_frame.update_idletasks()
        if hasattr(self, "macro_tabs_canvas"):
            self.macro_tabs_canvas.configure(
                scrollregion=self.macro_tabs_canvas.bbox("all")
            )
            # Show/hide scroll buttons based on content width
            canvas_width = self.macro_tabs_canvas.winfo_width()
            content_width = self.macro_tabs_frame.winfo_reqwidth()
            if content_width > canvas_width and canvas_width > 1:
                self.macro_scroll_left.pack(side="left", before=self.macro_tabs_canvas)
                self.macro_scroll_right.pack(
                    side="left", after=self.macro_tabs_canvas, before=self.macro_add_btn
                )
            else:
                self.macro_scroll_left.pack_forget()
                self.macro_scroll_right.pack_forget()

    def _scroll_macro_tabs(self, direction):
        """Scroll macro tabs left or right"""
        self.macro_tabs_canvas.xview_scroll(direction * 3, "units")

    def _update_macro_entry_colors(self):
        """Update Entry widget colors to match current theme"""
        bg_light = self.colors["bg_light"]
        text = self.colors["text"]
        # Update name entry
        if hasattr(self, "macro_name_entry"):
            self.macro_name_entry.config(
                bg=bg_light,
                fg=text,
                insertbackground=text,
                highlightbackground=self.colors.get("bg_lighter", "#555555"),
            )
        # Update hotkey entry
        if hasattr(self, "macro_hotkey_entry"):
            self.macro_hotkey_entry.config(
                bg=bg_light, fg=text, readonlybackground=bg_light
            )

    def _on_macro_tab_click(self, index):
        """Switch to a different macro tab"""
        # Save current macro first
        self._save_current_macro_from_ui()
        # Switch to new index
        self.active_macro_index = index
        self.custom_macros_data["active_index"] = index
        save_custom_macros(self.custom_macros_data)
        # Rebuild tabs to update visual state
        self._build_macro_tabs()
        # Load new macro into UI
        self._load_current_macro_to_ui()


# quickdupe.py
from quickdupe_ui import QuickDupeUI

class QuickDupeApp:
    def __init__(self, root):
        # ... init ...
        self.ui = QuickDupeUI(self, root, self.colors, self.config)
        self.ui.build_ui()
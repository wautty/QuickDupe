# Änderungsbeispiele (Vorher/Nachher)

Dieses Dokument zeigt **echte Beispiele aus dem Code** mit jeweils einer **Vorher‑Codezeile** und der **Änderung danach**.

> Stand: 2026‑02‑09

---

## 1) Netzwerkfunktionen ausgelagert (`quickdupe.py` → `utils/network.py`)

### Vorher (in `quickdupe.py`)

```python
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
```

### Nachher (in `quickdupe.py` + neues Modul)

```python
from utils.network import (
    start_packet_drop,
    stop_packet_drop,
    is_dropping,
    start_packet_tamper,
    stop_packet_tamper,
    is_tampering,
)
```

Und die Logik liegt jetzt zentral in `utils/network.py`:

```python
def start_packet_drop(outbound=True, inbound=True):
    """DROP PACKETS NOW"""
    global _handle, _on, _pydivert
    if _on:
        return
    if _pydivert is None:
        import pydivert
        _pydivert = pydivert
```

---

## 2) Export All speichert komplette Config + Macros

### Vorher (nur Triggernade & Mine)

```python
if path:
    data = {
        "type": "all",
        "triggernade": self._get_triggernade_settings(),
        "mine": self._get_mine_settings(),
    }
```

### Nachher (vollständige Config + Custom Macros)

```python
if path:
    # Ensure config is up-to-date with current UI values
    self.save_settings()
    data = {
        "type": "all",
        "config": self.config,
        "custom_macros": self.custom_macros_data,
        "triggernade": self._get_triggernade_settings(),
        "mine": self._get_mine_settings(),
    }
```

---

## 3) Import All aktualisiert UI‑Zustand

### Vorher (nur Teil‑Settings)

```python
if data.get("type") == "all":
    if "triggernade" in data:
        self._set_triggernade_settings(data["triggernade"])
    if "mine" in data:
        self._set_mine_settings(data["mine"])
```

### Nachher (Config + UI‑Sync + Macros)

```python
if data.get("type") == "all":
    if "config" in data:
        self.config = data["config"]
        save_config(self.config)
        self._apply_config_to_ui()
    if "custom_macros" in data:
        self.custom_macros_data = data["custom_macros"]
        save_custom_macros(self.custom_macros_data)
        self._build_macro_tabs()
        self._load_current_macro_to_ui()
    if "triggernade" in data:
        self._set_triggernade_settings(data["triggernade"])
    if "mine" in data:
        self._set_mine_settings(data["mine"])
```

---

## 4) Fehlende Timing‑Werte werden in `save_settings()` gespeichert

### Vorher (Auszug – fehlende Keys)

```python
self.config["trig_m1_hold"] = self.trig_m1_hold_var.get()
self.config["trig_m2_hold"] = self.trig_m2_hold_var.get()
self.config["trig_dc_delay"] = self.trig_dc_delay_var.get()
```

### Nachher (zusätzliche Keys inkl. Drag‑Speed & Interweave)

```python
self.config["trig_m1_hold"] = self.trig_m1_hold_var.get()
self.config["trig_m2_hold"] = self.trig_m2_hold_var.get()
self.config["trig_drag_speed"] = self.trig_drag_speed_var.get()
self.config["trig_dc_delay"] = self.trig_dc_delay_var.get()
self.config["trig_m1_before_interweave"] = self.trig_m1_before_interweave_var.get()
```

### Vorher (Mine‑Block ohne zusätzliche Werte)

```python
self.config["mine_cook"] = self.mine_cook_var.get()
self.config["mine_dc_delay"] = self.mine_dc_delay_var.get()
self.config["mine_click_delay"] = self.mine_click_delay_var.get()
```

### Nachher (Mine‑Block inkl. Drag/Close/Tab‑Zeiten)

```python
self.config["mine_cook"] = self.mine_cook_var.get()
self.config["mine_dc_delay"] = self.mine_dc_delay_var.get()
self.config["mine_drag_speed"] = self.mine_drag_speed_var.get()
self.config["mine_pre_close"] = self.mine_pre_close_var.get()
self.config["mine_tab_hold"] = self.mine_tab_hold_var.get()
self.config["mine_close_reconnect"] = self.mine_close_reconnect_var.get()
self.config["mine_click_delay"] = self.mine_click_delay_var.get()
```

### Vorher (E‑Drop ohne E+DC‑Delay)

```python
self.config["edrop_e_press"] = self.edrop_e_press_var.get()
self.config["edrop_wait_before_inv"] = self.edrop_wait_before_inv_var.get()
```

### Nachher (E+DC‑Delay wird gespeichert)

```python
self.config["edrop_e_press"] = self.edrop_e_press_var.get()
self.config["edrop_e_dc_delay"] = self.edrop_e_dc_delay_var.get()
self.config["edrop_wait_before_inv"] = self.edrop_wait_before_inv_var.get()
```

---

## 5) UI‑Sync Helfer nach Import

### Vorher

```python
# (Kein zentraler Sync vorhanden)
```

### Nachher (neue Methode)

```python
def _apply_config_to_ui(self):
    """Apply self.config values to UI variables and state"""
    config = self.config or {}
    for key, value in config.items():
        var_name = f"{key}_var"
        if hasattr(self, var_name):
            getattr(self, var_name).set(value)
```

---

## Hinweise

- Config‑Dateien liegen unter:
  - `C:\Users\<Name>\AppData\Roaming\QuickDupe\config.json`
  - `C:\Users\<Name>\AppData\Roaming\QuickDupe\custom_macros.json`

Wenn du weitere Beispiele brauchst, sag Bescheid – ich ergänze sie gerne.

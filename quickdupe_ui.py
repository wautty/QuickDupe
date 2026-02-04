# quickdupe_ui.py
class QuickDupeUI:
    def __init__(self, app, root, colors, config):
        self.app = app  # Referenz zur Haupt-App
        self.root = root
        self.colors = colors
        self.config = config
        
    def build_ui(self):
        # Alle UI-Erstellung hier
        pass

# quickdupe.py
from quickdupe_ui import QuickDupeUI

class QuickDupeApp:
    def __init__(self, root):
        # ... init ...
        self.ui = QuickDupeUI(self, root, self.colors, self.config)
        self.ui.build_ui()
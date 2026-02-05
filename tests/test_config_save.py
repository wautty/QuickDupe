"""
Test script to verify all GUI settings are saved to config
"""
import re
from pathlib import Path

# Read the quickdupe.py file
quickdupe_path = Path(__file__).parent / "quickdupe.py"
with open(quickdupe_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find all StringVar/IntVar declarations (GUI variables)
# Patterns: self.xxx_var = tk.StringVar(...) or tk.IntVar(...)
var_pattern = r'self\.(\w+_var)\s*=\s*tk\.(StringVar|IntVar)'
gui_vars = set(re.findall(var_pattern, content))
gui_var_names = {var[0] for var in gui_vars}

print(f"Found {len(gui_var_names)} GUI variables")
print("="*60)

# Find all variables saved in save_settings()
# Find the save_settings function
save_settings_match = re.search(
    r'def save_settings\(self\):(.+?)(?=\n    def |\Z)', 
    content, 
    re.DOTALL
)

if not save_settings_match:
    print("ERROR: Could not find save_settings() function!")
    exit(1)

save_settings_body = save_settings_match.group(1)

# Find all self.config["xxx"] = self.xxx_var.get() patterns
config_save_pattern = r'self\.config\["(\w+)"\]\s*=\s*.*?self\.(\w+_var)\.get\(\)'
saved_vars = re.findall(config_save_pattern, save_settings_body)

saved_var_names = {var[1] for var in saved_vars}
saved_config_keys = {var[0] for var in saved_vars}

print(f"Found {len(saved_var_names)} variables saved in save_settings()")
print("="*60)

# Also find position variables (special case: list(...))
position_pattern = r'self\.config\["(\w+)"\]\s*=\s*list\(self\.(\w+)\)'
position_vars = re.findall(position_pattern, save_settings_body)
position_var_names = {var[1] for var in position_vars}

print(f"Found {len(position_var_names)} position variables saved")
print("="*60)

# Find variables that are NOT saved
missing_vars = gui_var_names - saved_var_names

# Filter out some special variables that shouldn't be saved
excluded_patterns = [
    '_status_var',  # Status display variables
    '_pos_var',     # Position display variables (RClick:... Drop:...)
    '_recording_',  # Recording state variables
]

filtered_missing = []
for var in missing_vars:
    should_exclude = False
    for pattern in excluded_patterns:
        if pattern in var:
            should_exclude = True
            break
    if not should_exclude:
        filtered_missing.append(var)

if filtered_missing:
    print("\n⚠️  MISSING VARIABLES (not saved in save_settings()):")
    print("="*60)
    for var in sorted(filtered_missing):
        print(f"  - {var}")
    print()
else:
    print("\n✅ All relevant GUI variables are saved!")
    print()

# Show what IS being saved
print("\n📝 Variables currently saved in save_settings():")
print("="*60)
for config_key, var_name in sorted(saved_vars):
    print(f"  {config_key:40} <- {var_name}")

if position_vars:
    print("\n📍 Position variables saved:")
    print("="*60)
    for config_key, var_name in sorted(position_vars):
        print(f"  {config_key:40} <- {var_name}")

# Summary
print("\n" + "="*60)
print("SUMMARY:")
print(f"  Total GUI variables:        {len(gui_var_names)}")
print(f"  Saved in save_settings():   {len(saved_var_names)}")
print(f"  Position variables saved:   {len(position_var_names)}")
print(f"  Missing (filtered):         {len(filtered_missing)}")
print("="*60)

if filtered_missing:
    exit(1)  # Exit with error if missing variables
else:
    exit(0)  # Success

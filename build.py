#!/usr/bin/env python3
"""
Build script that generates a unique signature for each compilation.
Each person who builds gets their own unique watermark.
"""
import subprocess
import uuid
import random
import string
import os
import sys

SOURCE_FILE = "quickdupe.py"
SPEC_FILE = "QuickDupe.spec"
PLACEHOLDER = "__BUILD_ID_PLACEHOLDER__"

def generate_signature():
    """Generate a unique signature - UUID + random string"""
    # UUID for uniqueness
    uid = str(uuid.uuid4()).replace('-', '').upper()[:8]
    # Random string for extra randomness
    rand = ''.join(random.choices(string.ascii_letters, k=10))
    return f"{uid}-{rand}"

def build():
    # Generate unique signature
    signature = generate_signature()
    print(f"[BUILD] Generated unique signature: {signature}")

    # Read source
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        original_source = f.read()

    if PLACEHOLDER not in original_source:
        print("[ERROR] Placeholder not found in source! Already built?")
        print("        Reset the BUILD_ID line to: BUILD_ID = \"__BUILD_ID_PLACEHOLDER__\"")
        sys.exit(1)

    # Replace placeholder with unique signature
    modified_source = original_source.replace(PLACEHOLDER, signature)

    # Write modified source
    with open(SOURCE_FILE, 'w', encoding='utf-8') as f:
        f.write(modified_source)

    print(f"[BUILD] Injected signature into {SOURCE_FILE}")

    try:
        # Run PyInstaller
        print("[BUILD] Running PyInstaller...")
        result = subprocess.run(
            ["pyinstaller", SPEC_FILE, "--noconfirm"],
            check=True
        )
        print(f"[BUILD] Success! Signature: {signature}")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] PyInstaller failed: {e}")
    finally:
        # Restore original source (keep git clean)
        with open(SOURCE_FILE, 'w', encoding='utf-8') as f:
            f.write(original_source)
        print(f"[BUILD] Restored {SOURCE_FILE} to original state")

if __name__ == "__main__":
    build()

"""
prepare_vendor.py — Run this ONCE on the developer machine before building the .exe.

Copies the Tesseract-OCR binaries from your local installation into vendor/tesseract/
so they can be bundled by PyInstaller and shipped with the app.

Usage:
    python prepare_vendor.py
    python prepare_vendor.py --tess-path "C:/MyCustomPath/Tesseract-OCR"
"""

import argparse
import os
import shutil
import sys

SEARCH_PATHS = [
    r"C:\Program Files\Tesseract-OCR",
    r"C:\Program Files (x86)\Tesseract-OCR",
    r"C:\Tesseract-OCR",
    r"C:\tools\Tesseract-OCR",
]

VENDOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor", "tesseract")
TESSDATA_FILES = ["eng.traineddata", "osd.traineddata"]


def find_tesseract(custom_path: str | None = None) -> str | None:
    if custom_path:
        exe = os.path.join(custom_path, "tesseract.exe")
        if os.path.isfile(exe):
            return custom_path
        print(f"[!] tesseract.exe not found at: {custom_path}")
        return None

    for path in SEARCH_PATHS:
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "tesseract.exe")):
            return path

    # Try PATH
    on_path = shutil.which("tesseract")
    if on_path:
        return os.path.dirname(on_path)

    return None


def copy_tesseract(tess_dir: str):
    print(f"Source: {tess_dir}")
    print(f"Target: {VENDOR_DIR}")

    if os.path.exists(VENDOR_DIR):
        shutil.rmtree(VENDOR_DIR)
    os.makedirs(VENDOR_DIR, exist_ok=True)

    # Copy tesseract.exe and all DLLs from the root directory
    copied_files = 0
    for fname in os.listdir(tess_dir):
        if fname.lower().endswith((".exe", ".dll")):
            src = os.path.join(tess_dir, fname)
            shutil.copy2(src, VENDOR_DIR)
            copied_files += 1

    print(f"  Copied {copied_files} binaries (exe + dlls)")

    # Copy only the needed tessdata files (eng + osd)
    tessdata_src = os.path.join(tess_dir, "tessdata")
    tessdata_dst = os.path.join(VENDOR_DIR, "tessdata")
    os.makedirs(tessdata_dst, exist_ok=True)

    copied_data = 0
    for fname in TESSDATA_FILES:
        src = os.path.join(tessdata_src, fname)
        if os.path.isfile(src):
            shutil.copy2(src, tessdata_dst)
            copied_data += 1
        else:
            print(f"  [!] Missing tessdata file: {fname} (OCR may not work)")

    print(f"  Copied {copied_data}/{len(TESSDATA_FILES)} tessdata files")


def main():
    parser = argparse.ArgumentParser(description="Prepare Tesseract vendor files for bundling.")
    parser.add_argument("--tess-path", default=None, help="Custom Tesseract install directory")
    args = parser.parse_args()

    print("=" * 50)
    print("TheFinalsStats — Vendor Preparation")
    print("=" * 50)

    tess_dir = find_tesseract(args.tess_path)
    if not tess_dir:
        print()
        print("[ERROR] Tesseract-OCR not found on this machine.")
        print()
        print("Please install it first:")
        print("  https://github.com/UB-Mannheim/tesseract/wiki")
        print()
        print("Or specify the path manually:")
        print('  python prepare_vendor.py --tess-path "C:\\path\\to\\Tesseract-OCR"')
        sys.exit(1)

    print(f"Found Tesseract at: {tess_dir}")
    print()
    copy_tesseract(tess_dir)

    print()
    print("[OK] vendor/tesseract/ is ready.")
    print("     You can now run build.bat to create the .exe")


if __name__ == "__main__":
    main()

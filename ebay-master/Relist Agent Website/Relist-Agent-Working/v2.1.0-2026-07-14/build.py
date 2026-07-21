#!/usr/bin/env python3
"""
Build script for Relist Agent v2.0.0
Converts gui_app.py into a standalone .exe using PyInstaller
"""

import subprocess
import sys
import shutil
import os
from pathlib import Path

def run_command(cmd, desc, use_shell=True):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f">> {desc}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=use_shell, check=True)
        print(f"[OK] {desc} completed\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {desc} failed with exit code {e.returncode}\n")
        return False

def main():
    project_dir = Path(__file__).parent
    dist_dir = project_dir / "dist"
    build_dir = project_dir / "build"
    icon_file = project_dir / "ERA_Icon.png"

    print("\n" + "="*60)
    print("  RELIST AGENT v2.0.0 - EXE BUILD")
    print("="*60)

    # Check PyInstaller is installed
    print("\n>> Checking PyInstaller installation...")
    result = subprocess.run("pyinstaller --version", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("[FAIL] PyInstaller not found. Install with: pip install pyinstaller")
        sys.exit(1)
    print(f"[OK] {result.stdout.strip()}\n")

    # Clean old builds
    print(">> Cleaning old builds...")
    for d in [dist_dir, build_dir]:
        if d.exists():
            shutil.rmtree(d)
            print(f"  Removed {d.name}/")

    # Build EXE
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--icon={icon_file}",
        "--name=Relist Agent",
        "gui_app.py"
    ]

    if not run_command(cmd, "Building EXE with PyInstaller", use_shell=False):
        sys.exit(1)

    # Verify output
    exe_path = dist_dir / "Relist Agent.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024**2)
        print(f"\n{'='*60}")
        print(f"[SUCCESS] BUILD COMPLETE")
        print(f"{'='*60}")
        print(f"\nOutput: {exe_path}")
        print(f"Size: {size_mb:.1f} MB")
        print(f"\nNext steps:")
        print(f"  1. Test the EXE: double-click {exe_path}")
        print(f"  2. Verify license validation works (app-specific enforcement)")
        print(f"  3. When satisfied, deploy to production")
        print(f"\n{'='*60}\n")
    else:
        print(f"\n[FAIL] Build failed: {exe_path} not found")
        sys.exit(1)

if __name__ == "__main__":
    main()

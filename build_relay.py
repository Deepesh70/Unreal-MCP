"""
Unreal MCP Relay Build Script — Packages the Python server into a standalone executable.

Usage:
    python build_relay.py              # PyInstaller build (Fast for testing)
    python build_relay.py --nuitka     # Nuitka C++ build (Secure for production)

Outputs:
    dist/UnrealMCP_Relay.exe
    Also copies to unrealui/public/downloads/UnrealMCP_Relay.exe for web serving.
"""

import sys
import os
import shutil
import subprocess
import argparse

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ENTRY_POINT = os.path.join(PROJECT_ROOT, "server.py")
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
WEB_DOWNLOADS_DIR = os.path.normpath(
    os.path.join(PROJECT_ROOT, "..", "UnrealMCP_UI", "unrealui", "public", "downloads")
)


def build_pyinstaller():
    """Build standalone executable using PyInstaller."""
    try:
        import PyInstaller  # Check availability
    except ImportError:
        print("⚠ PyInstaller is not installed in your Python environment.")
        print("   Installing PyInstaller now...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Remove obsolete third-party pathlib package if present (causes PyInstaller conflict in Anaconda)
    try:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "pathlib"], capture_output=True)
    except Exception:
        pass

    print("🚀 Building UnrealMCP_Relay.exe using PyInstaller...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name=UnrealMCP_Relay",
        "--clean",
        "--collect-all=unreal_mcp",
        "--collect-all=fastmcp",
        ENTRY_POINT
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ PyInstaller build completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller build failed: {e}")
        sys.exit(1)


def build_nuitka():
    """Build C++ compiled machine-code binary using Nuitka."""
    try:
        import nuitka  # Check availability
    except ImportError:
        print("⚠ Nuitka is not installed in your Python environment.")
        print("   Installing Nuitka now...")
        subprocess.run([sys.executable, "-m", "pip", "install", "nuitka"], check=True)

    print("🔒 Building secure C++ UnrealMCP_Relay.exe using Nuitka...")
    
    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--standalone",
        "--output-filename=UnrealMCP_Relay.exe",
        "--include-package=unreal_mcp",
        "--include-package=fastmcp",
        "--assume-yes-for-downloads",
        ENTRY_POINT
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ Nuitka C++ compilation completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Nuitka build failed: {e}")
        sys.exit(1)


def sync_to_website():
    """Copy the generated binary to the Next.js public downloads directory."""
    exe_src = os.path.join(DIST_DIR, "UnrealMCP_Relay.exe")
    
    if not os.path.exists(exe_src):
        # Nuitka might place it directly in root
        exe_src = os.path.join(PROJECT_ROOT, "UnrealMCP_Relay.exe")
        
    if os.path.exists(exe_src):
        os.makedirs(WEB_DOWNLOADS_DIR, exist_ok=True)
        dest = os.path.join(WEB_DOWNLOADS_DIR, "UnrealMCP_Relay.exe")
        shutil.copy2(exe_src, dest)
        print(f"📦 Synced executable to Web UI downloads: {dest}")
    else:
        print("⚠ Executable not found for web sync.")


def main():
    parser = argparse.ArgumentParser(description="Build Unreal MCP Relay Executable")
    parser.add_argument("--nuitka", action="store_true", help="Use Nuitka C++ compiler for production security")
    args = parser.parse_args()

    if args.nuitka:
        build_nuitka()
    else:
        build_pyinstaller()
        
    sync_to_website()


if __name__ == "__main__":
    main()

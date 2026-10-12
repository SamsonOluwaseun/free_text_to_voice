"""
Samlytics VoiceStudio Uninstaller.
Safely removes:
1. Desktop shortcut (including OneDrive redirects)
2. Windows Start Menu shortcut
3. Windows Programs & Features (Installed Apps) Registry entry
4. Optional uninstallation of Python package dependencies
"""

import os
import sys
import subprocess
import ctypes
import ctypes.wintypes
from register_app import unregister_from_windows_programs

APP_NAME = "Samlytics VoiceStudio"

def get_desktop_dir():
    try:
        CSIDL_DESKTOP = 0
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, 0, buf)
        if buf.value and os.path.exists(buf.value):
            return buf.value
    except Exception:
        pass
    
    # Check OneDrive Desktop fallback
    user_prof = os.environ.get("USERPROFILE", "")
    onedrive_dt = os.path.join(user_prof, "OneDrive", "Desktop")
    if os.path.exists(onedrive_dt):
        return onedrive_dt
    
    return os.path.join(user_prof, "Desktop")

def get_start_menu_dir():
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs")

def remove_shortcuts():
    removed = 0
    # 1. Desktop shortcut
    dt_dir = get_desktop_dir()
    dt_shortcut = os.path.join(dt_dir, f"{APP_NAME}.lnk")
    if os.path.exists(dt_shortcut):
        try:
            os.remove(dt_shortcut)
            print(f"[x] Removed Desktop shortcut: {dt_shortcut}")
            removed += 1
        except Exception as e:
            print(f"[!] Could not remove Desktop shortcut: {e}")

    # Also check standard desktop if OneDrive was primary
    std_dt = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", f"{APP_NAME}.lnk")
    if os.path.exists(std_dt) and std_dt != dt_shortcut:
        try:
            os.remove(std_dt)
            print(f"[x] Removed standard Desktop shortcut: {std_dt}")
            removed += 1
        except Exception:
            pass

    # 2. Start Menu shortcut
    sm_dir = get_start_menu_dir()
    sm_shortcut = os.path.join(sm_dir, f"{APP_NAME}.lnk")
    if os.path.exists(sm_shortcut):
        try:
            os.remove(sm_shortcut)
            print(f"[x] Removed Start Menu shortcut: {sm_shortcut}")
            removed += 1
        except Exception as e:
            print(f"[!] Could not remove Start Menu shortcut: {e}")

    if removed == 0:
        print("[i] No shortcuts found to remove.")
    return removed

def uninstall_dependencies():
    packages = ["customtkinter", "sounddevice", "soundfile", "edge-tts", "pygame", "pydub", "librosa"]
    print(f"\nUninstalling Python packages: {', '.join(packages)}...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y"] + packages, check=False)
        print("[x] Dependencies uninstalled successfully.")
    except Exception as e:
        print(f"[!] Could not uninstall packages: {e}")

def run_uninstall(quiet=False, remove_deps=False):
    print("=" * 60)
    print("      SAMLYTICS VOICE STUDIO - UNINSTALLER")
    print("=" * 60)

    # 1. Remove shortcuts
    print("\n[1/3] Removing desktop and start menu shortcuts...")
    remove_shortcuts()

    # 2. Unregister from Windows Installed Apps
    print("\n[2/3] Unregistering from Windows Installed Programs...")
    unregister_from_windows_programs()

    # 3. Handle Python Dependencies
    if remove_deps:
        uninstall_dependencies()
    elif not quiet:
        print("\n[3/3] Python dependencies:")
        choice = input("Do you also want to uninstall Python packages (pip)? (y/N): ").strip().lower()
        if choice in ("y", "yes"):
            uninstall_dependencies()
        else:
            print("Kept Python packages (so other Python projects are unaffected).")
    else:
        print("\n[3/3] Kept Python packages.")

    print("\n" + "=" * 60)
    print("  SAMLYTICS VOICE STUDIO UNINSTALLATION COMPLETE!")
    print("  The app is removed from your Desktop and Windows Programs.")
    print("  To completely delete all project files, you may now delete")
    print("  this folder.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    is_quiet = "/quiet" in sys.argv or "--quiet" in sys.argv or "-q" in sys.argv
    clean_deps = "--remove-deps" in sys.argv
    run_uninstall(quiet=is_quiet, remove_deps=clean_deps)


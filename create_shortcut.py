"""
Desktop Shortcut Creator for Samlytics VoiceStudio.
Automatically resolves the active user desktop (including OneDrive redirects),
creates a Windows shortcut targeting pythonw.exe (so no console window appears),
and assigns the official Samlytics brand icon.
"""

import os
import sys
import subprocess
import ctypes
import ctypes.wintypes

def create_desktop_shortcut():
    try:
        # Resolve Windows Desktop path
        CSIDL_DESKTOP = 0
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, 0, buf)
        desktop_dir = buf.value
    except Exception:
        desktop_dir = os.path.join(os.environ.get("USERPROFILE", "."), "Desktop")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "app_icon.ico")
    app_script = os.path.join(base_dir, "app.py")

    # Use pythonw.exe so no black command prompt window stays open
    python_dir = os.path.dirname(sys.executable)
    pythonw_path = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw_path):
        pythonw_path = sys.executable

    shortcut_path = os.path.join(desktop_dir, "Samlytics VoiceStudio.lnk")

    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = pythonw_path
        shortcut.Arguments = f'"{app_script}"'
        shortcut.WorkingDirectory = base_dir
        if os.path.exists(icon_path):
            shortcut.IconLocation = f"{icon_path},0"
        shortcut.Description = "Samlytics VoiceStudio — Local Text-to-Voice & Storytelling Studio"
        shortcut.save()
    except Exception:
        # Fail-safe native PowerShell shortcut creation
        ps_cmd = (
            f'$ws = New-Object -ComObject WScript.Shell; '
            f'$s = $ws.CreateShortcut("{shortcut_path}"); '
            f'$s.TargetPath = "{pythonw_path}"; '
            f'$s.Arguments = \'"{app_script}"\'; '
            f'$s.WorkingDirectory = "{base_dir}"; '
            f'$s.IconLocation = "{icon_path},0"; '
            f'$s.Description = "Samlytics VoiceStudio"; '
            f'$s.Save()'
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)

    print(f"SUCCESS: Created shortcut on your Desktop: {shortcut_path}")
    return shortcut_path

if __name__ == "__main__":
    create_desktop_shortcut()

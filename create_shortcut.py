"""
Desktop and Start Menu Shortcut Creator for Samlytics VoiceStudio.
Automatically resolves the active user desktop (including OneDrive redirects)
and Start Menu Programs folder, creates Windows shortcuts targeting pythonw.exe
(so no black console window appears), and assigns the official Samlytics brand icon.
"""

import os
import sys
import subprocess
import ctypes
import ctypes.wintypes

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
    
    user_prof = os.environ.get("USERPROFILE", "")
    onedrive_dt = os.path.join(user_prof, "OneDrive", "Desktop")
    if os.path.exists(onedrive_dt):
        return onedrive_dt
    
    return os.path.join(user_prof, "Desktop")

def get_start_menu_dir():
    appdata = os.environ.get("APPDATA", "")
    sm_dir = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs")
    if os.path.exists(sm_dir):
        return sm_dir
    return None

def write_shortcut(target_path, pythonw_path, app_script, base_dir, icon_path):
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(target_path)
        shortcut.TargetPath = pythonw_path
        shortcut.Arguments = f'"{app_script}"'
        shortcut.WorkingDirectory = base_dir
        if os.path.exists(icon_path):
            shortcut.IconLocation = f"{icon_path},0"
        shortcut.Description = "Samlytics VoiceStudio — Local Text-to-Voice & Storytelling Studio"
        shortcut.save()
    except Exception:
        ps_cmd = (
            f'$ws = New-Object -ComObject WScript.Shell; '
            f'$s = $ws.CreateShortcut("{target_path}"); '
            f'$s.TargetPath = "{pythonw_path}"; '
            f'$s.Arguments = \'"{app_script}"\'; '
            f'$s.WorkingDirectory = "{base_dir}"; '
            f'$s.IconLocation = "{icon_path},0"; '
            f'$s.Description = "Samlytics VoiceStudio"; '
            f'$s.Save()'
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)

def create_shortcuts():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "app_icon.ico")
    app_script = os.path.join(base_dir, "app.py")

    python_dir = os.path.dirname(sys.executable)
    pythonw_path = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw_path):
        pythonw_path = sys.executable

    # 1. Desktop Shortcut
    desktop_dir = get_desktop_dir()
    dt_shortcut = os.path.join(desktop_dir, f"{APP_NAME}.lnk")
    write_shortcut(dt_shortcut, pythonw_path, app_script, base_dir, icon_path)
    print(f"SUCCESS: Created shortcut on your Desktop: {dt_shortcut}")

    # 2. Start Menu Shortcut
    sm_dir = get_start_menu_dir()
    if sm_dir:
        sm_shortcut = os.path.join(sm_dir, f"{APP_NAME}.lnk")
        write_shortcut(sm_shortcut, pythonw_path, app_script, base_dir, icon_path)
        print(f"SUCCESS: Created shortcut in Windows Start Menu: {sm_shortcut}")

    # Notify Windows Explorer to immediately refresh desktop icon cache
    try:
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
    except Exception:
        pass

if __name__ == "__main__":
    create_shortcuts()

"""
Windows Programs & Features (Installed Apps) Registration
Registers Samlytics VoiceStudio in Windows Settings / Control Panel so users
can view, manage, and uninstall the program easily through native Windows tools.
"""

import os
import sys
import winreg

APP_NAME = "Samlytics VoiceStudio"
REG_SUBKEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\SamlyticsVoiceStudio"
VERSION = "1.0.0"
PUBLISHER = "Samlytics Data Services"
URL_ABOUT = "https://github.com/SamsonOluwaseun/free_text_to_voice"

def register_in_windows_programs():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "app_icon.ico")
    uninstall_bat = os.path.join(base_dir, "uninstall_app.bat")

    uninstall_cmd = f'cmd.exe /c call "{uninstall_bat}"'
    quiet_uninstall_cmd = f'cmd.exe /c call "{uninstall_bat}" /quiet'

    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_SUBKEY)
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, base_dir)
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
        winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, quiet_uninstall_cmd)
        winreg.SetValueEx(key, "URLInfoAbout", 0, winreg.REG_SZ, URL_ABOUT)
        winreg.SetValueEx(key, "HelpLink", 0, winreg.REG_SZ, URL_ABOUT)
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, 50000)

        if os.path.exists(icon_path):
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_path)

        winreg.CloseKey(key)
        print("SUCCESS: Registered Samlytics VoiceStudio in Windows Installed Programs.")
        return True
    except Exception as e:
        print(f"WARNING: Could not register in Windows Programs: {e}")
        return False

def unregister_from_windows_programs():
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_SUBKEY)
        print("SUCCESS: Unregistered Samlytics VoiceStudio from Windows Programs.")
        return True
    except FileNotFoundError:
        return True
    except Exception as e:
        print(f"WARNING: Could not unregister from Windows Programs: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--unregister":
        unregister_from_windows_programs()
    else:
        register_in_windows_programs()

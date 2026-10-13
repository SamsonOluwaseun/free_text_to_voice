"""
Release Packager for Samlytics VoiceStudio
Builds two separate, clean ZIP distributions:
1. dist/VoiceStudio-Desktop-v1.0.zip  (For Windows desktop users)
2. dist/VoiceStudio-MCP-AI-v1.0.zip   (For Claude Desktop, Cursor, and AI agents)
"""

import os
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
DIST_DIR = BASE_DIR / "dist"

DESKTOP_FILES = [
    "app.py",
    "install_app.bat",
    "run_app.bat",
    "create_shortcut.py",
    "register_app.py",
    "uninstall_app.bat",
    "uninstall_app.py",
    "tts_engine.py",
    "offline_engine.py",
    "audio_mixer.py",
    "voice_cloner.py",
    "recorder.py",
    "subtitle_engine.py",
    "model_manager.py",
    "tracks_generator.py",
    "requirements.txt",
    "README.md",
]

DESKTOP_DIRS = [
    "assets",
    "background_tracks",
    "offline_models",
]

MCP_AI_FILES = [
    "mcp_server.py",
    "cli.py",
    "tts_engine.py",
    "offline_engine.py",
    "audio_mixer.py",
    "subtitle_engine.py",
    "tracks_generator.py",
    "distill_dataset.py",
    "train_offline_abeo.ipynb",
    "SKILL.md",
    "setup.py",
    "requirements-mcp.txt",
    "README.md",
]

MCP_AI_DIRS = [
    "background_tracks",
    "offline_models",
]

def add_file_to_zip(zf, file_path, arcname):
    if file_path.exists():
        zf.write(file_path, arcname=arcname)

def add_dir_to_zip(zf, dir_path, base_prefix=""):
    if not dir_path.exists():
        return
    for root, _, files in os.walk(dir_path):
        for f in files:
            full_path = Path(root) / f
            rel_path = full_path.relative_to(BASE_DIR)
            arcname = f"{base_prefix}/{rel_path}" if base_prefix else str(rel_path)
            zf.write(full_path, arcname=arcname)

def package_desktop():
    zip_path = DIST_DIR / "VoiceStudio-Desktop-v1.0.zip"
    print(f"[*] Packaging Desktop Edition -> {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        folder_prefix = "VoiceStudio-Desktop"
        for fname in DESKTOP_FILES:
            fpath = BASE_DIR / fname
            add_file_to_zip(zf, fpath, f"{folder_prefix}/{fname}")
        for dname in DESKTOP_DIRS:
            dpath = BASE_DIR / dname
            add_dir_to_zip(zf, dpath, base_prefix=folder_prefix)
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[+] Desktop Edition packaged: {size_mb:.2f} MB")
    return zip_path

def package_mcp_ai():
    zip_path = DIST_DIR / "VoiceStudio-MCP-AI-v1.0.zip"
    print(f"[*] Packaging AI & MCP Edition -> {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        folder_prefix = "VoiceStudio-MCP-AI"
        for fname in MCP_AI_FILES:
            fpath = BASE_DIR / fname
            arcname = f"{folder_prefix}/requirements.txt" if fname == "requirements-mcp.txt" else f"{folder_prefix}/{fname}"
            add_file_to_zip(zf, fpath, arcname)
        for dname in MCP_AI_DIRS:
            dpath = BASE_DIR / dname
            add_dir_to_zip(zf, dpath, base_prefix=folder_prefix)
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[+] AI & MCP Edition packaged: {size_mb:.2f} MB")
    return zip_path

def main():
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("  SAMLYTICS VOICESTUDIO — DUAL RELEASE PACKAGER")
    print("=" * 60)
    package_desktop()
    package_mcp_ai()
    print("=" * 60)
    print(f"SUCCESS: Both packages generated in {DIST_DIR.resolve()}")
    print("=" * 60)

if __name__ == "__main__":
    main()


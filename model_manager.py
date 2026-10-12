"""
Model & Deep AI Engine Manager.
Manages the optional Tier 2 Deep Neural Voice Cloning upgrade.
Allows users to run the fast, lightweight Tier 1 app by default,
while providing an optional in-app 1-click installer with clear
memory/disk requirements if they desire deep neural cloning.
"""

import importlib.util
import os
import subprocess
import sys
import threading

class ModelManager:
    @staticmethod
    def get_system_requirements() -> dict:
        return {
            "name": "Deep Neural Voice Cloning Engine (F5-TTS)",
            "disk_required_gb": 1.5,
            "ram_required_gb": 4.0,
            "speed_note": "~30-60 seconds on CPU per paragraph",
            "tier_description": "Generates flow-matched zero-shot speech replication."
        }

    @staticmethod
    def is_deep_engine_installed() -> bool:
        """Checks if optional deep AI cloning engine is installed."""
        f5_spec = importlib.util.find_spec("f5_tts")
        torch_spec = importlib.util.find_spec("torch")
        return f5_spec is not None and torch_spec is not None

    @classmethod
    def install_deep_engine_async(cls, on_progress=None, on_success=None, on_error=None):
        """
        Runs pip install in a background daemon thread.
        Notifies callbacks with progress strings.
        """
        def _worker():
            try:
                if on_progress:
                    on_progress("Downloading & configuring Deep AI Engine (~1.5GB)... This may take 2-3 minutes.")

                py_cmd = sys.executable
                cmd = [py_cmd, "-m", "pip", "install", "f5-tts", "torch", "torchaudio"]

                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in proc.stdout:
                    clean_line = line.strip()
                    if clean_line and on_progress:
                        # Forward significant progress updates
                        if any(k in clean_line.lower() for k in ["downloading", "installing", "collecting"]):
                            on_progress(clean_line[:65] + "...")

                proc.wait()

                if proc.returncode == 0:
                    if on_success:
                        on_success()
                else:
                    if on_error:
                        on_error(f"Installation exited with code {proc.returncode}")
            except Exception as e:
                if on_error:
                    on_error(str(e))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t


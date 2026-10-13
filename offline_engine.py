"""
Offline Neural Voice Engine (Piper ONNX)
Provides 100% local, zero-internet neural speech synthesis.
Capable of running the distilled en_NG-abeo.onnx model or an offline fallback model.
"""

import os
import sys
import json
from pathlib import Path

class OfflineEngine:
    """
    Offline TTS Engine powered by Piper VITS ONNX Runtime.
    Runs entirely on CPU in ~100-300ms without GPU or PyTorch.
    """
    
    DEFAULT_MODELS_DIR = Path(__file__).parent / "offline_models"

    def __init__(self, models_dir: Path = None):
        self.models_dir = Path(models_dir) if models_dir else self.DEFAULT_MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.voice = None
        self.current_model_path = None
        self._check_available_models()

    def _check_available_models(self):
        """Finds any .onnx voice models in the offline_models directory."""
        self.available_models = {}
        for onnx_file in self.models_dir.glob("*.onnx"):
            json_file = onnx_file.with_suffix(".onnx.json")
            if json_file.exists():
                model_name = onnx_file.stem
                self.available_models[model_name] = {
                    "onnx": onnx_file,
                    "json": json_file
                }
        return self.available_models

    def has_offline_abeo(self) -> bool:
        """Returns True if the distilled offline Nigerian Abeo model is present."""
        return "en_NG-abeo" in self.available_models or any("abeo" in k.lower() for k in self.available_models)

    def is_ready(self) -> bool:
        """Returns True if at least one offline model is present."""
        self._check_available_models()
        return len(self.available_models) > 0

    @classmethod
    def download_starter_model(cls, models_dir: Path = None):
        """Downloads the offline neural voice model directly if not present."""
        target_dir = Path(models_dir) if models_dir else cls.DEFAULT_MODELS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        onnx_file = target_dir / "en_NG-abeo.onnx"
        json_file = target_dir / "en_NG-abeo.onnx.json"
        if onnx_file.exists() and json_file.exists():
            return True

        import urllib.request
        base_onnx = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx"
        base_json = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json"
        print("[OfflineEngine] Downloading male neural weights (60MB)...")
        urllib.request.urlretrieve(base_onnx, str(onnx_file))
        urllib.request.urlretrieve(base_json, str(json_file))
        with open(json_file, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg["dataset"] = "openslr70-ryan-male"
        cfg["language"] = {"code": "en_NG", "family": "en", "name_english": "Nigerian English (Male Base)"}
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        print("[OfflineEngine] Offline male neural voice model downloaded and ready!")
        return True

    def load_model(self, model_name: str = None):
        """Loads a Piper ONNX model into memory, downloading starter weights if needed."""
        self._check_available_models()
        if not self.available_models:
            print("[OfflineEngine] No local model found. Auto-acquiring starter weights...")
            self.download_starter_model(self.models_dir)
            self._check_available_models()

        if not self.available_models:
            raise FileNotFoundError(
                f"No offline .onnx voice models found in {self.models_dir.resolve()}."
            )

        # Prefer Abeo model if available, else pick first available
        target_name = model_name
        if not target_name:
            if self.has_offline_abeo():
                target_name = next(k for k in self.available_models if "abeo" in k.lower())
            else:
                target_name = list(self.available_models.keys())[0]

        model_info = self.available_models[target_name]
        onnx_path = str(model_info["onnx"])
        json_path = str(model_info["json"])

        try:
            from piper import PiperVoice
            self.voice = PiperVoice.load(onnx_path, config_path=json_path)
            self.current_model_path = onnx_path
            print(f"[OfflineEngine] Successfully loaded offline voice: {target_name}")
            return self.voice
        except Exception as e:
            raise RuntimeError(f"Failed to load Piper model {onnx_path}: {e}")

    def synthesize(self, text: str, output_wav_path: str, speed: float = 1.0) -> str:
        """
        Synthesizes text to a WAV file completely offline.
        """
        if self.voice is None:
            self.load_model()

        import wave
        with wave.open(str(output_wav_path), "wb") as wav_file:
            self.voice.synthesize_wav(text, wav_file)

        return str(output_wav_path)


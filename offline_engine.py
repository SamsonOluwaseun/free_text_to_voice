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

    def load_model(self, model_name: str = None):
        """Loads a Piper ONNX model into memory."""
        self._check_available_models()
        if not self.available_models:
            raise FileNotFoundError(
                f"No offline .onnx voice models found in {self.models_dir.resolve()}. "
                "Please place en_NG-abeo.onnx and its config json in this directory."
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

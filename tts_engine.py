"""
Text-to-Speech Engine module.
Supports 4 distinct voice presets:
1. Deep Male
2. Soft Male
3. Professional Female 1
4. Professional Female 2
Provides voice texture (pitch/timbre) and speech speed rate controls.
Zero API keys, 100% free with edge-tts neural synthesis and offline Windows SAPI fallback.
"""

import asyncio
import os
import tempfile
import numpy as np
import soundfile as sf
import edge_tts
from offline_engine import OfflineEngine

VOICE_PRESETS = {
    "Nigerian Professional Male": {
        "id": "en-NG-AbeoNeural",
        "description": "Clear, engaging, articulate Nigerian accent — perfect for tutorials, tech explainers, and teaching complex concepts",
        "base_pitch_offset": 0,
        "offline_gender": "male"
    },
    "Deep Male": {
        "id": "en-US-ChristopherNeural",
        "description": "Authoritative, resonant, deep bass-baritone tone (ideal for documentaries & epic stories)",
        "base_pitch_offset": -5,
        "offline_gender": "male"
    },
    "Soft Male": {
        "id": "en-US-AndrewNeural",
        "description": "Gentle, warm, calm storytelling acoustic tone (ideal for bedtime stories & calm narration)",
        "base_pitch_offset": 0,
        "offline_gender": "male"
    },
    "Professional Female 1": {
        "id": "en-US-AvaNeural",
        "description": "Smooth, warm, natural conversational voice (ideal for audiobooks & podcasts)",
        "base_pitch_offset": 0,
        "offline_gender": "female"
    },
    "Professional Female 2": {
        "id": "en-US-AriaNeural",
        "description": "Crisp, bright, articulate executive tone (ideal for presentations & news)",
        "base_pitch_offset": +2,
        "offline_gender": "female"
    }
}

class TTSEngine:
    def __init__(self):
        self.last_boundaries = []
        try:
            self.offline_engine = OfflineEngine()
        except Exception:
            self.offline_engine = None

    def synthesize(self, text: str, voice_name: str, speed_mult: float = 1.0, texture_val: int = 0, force_offline: bool = False) -> tuple[np.ndarray, int]:
        """
        Synthesizes text to speech.
        
        Args:
            text: Text to speak.
            voice_name: One of the 4 keys in VOICE_PRESETS.
            speed_mult: Speed factor (0.5 to 2.0). 1.0 is normal.
            texture_val: Texture / Pitch adjustment in Hz (-20 to +20).
                         Negative = deeper / warmer tone, Positive = crisp / bright tone.
            force_offline: If True, uses local neural/offline synthesis.
                         
        Returns:
            (audio_numpy_array, sample_rate)
        """
        text = text.strip()
        if not text:
            raise ValueError("Input text is empty.")

        self.last_boundaries = []
        preset = VOICE_PRESETS.get(voice_name, VOICE_PRESETS["Deep Male"])
        voice_id = preset["id"]

        if force_offline:
            return self._synthesize_offline(text, preset, speed_mult, voice_name)

        # Calculate rate string for edge-tts (e.g. "+15%", "-20%")
        rate_percent = int(round((speed_mult - 1.0) * 100))
        rate_str = f"{rate_percent:+d}%"

        # Calculate pitch string for edge-tts (base preset offset + user slider)
        total_pitch_hz = int(preset["base_pitch_offset"] + texture_val)
        pitch_str = f"{total_pitch_hz:+d}Hz"

        try:
            return self._synthesize_edge_tts(text, voice_id, rate_str, pitch_str)
        except Exception as e:
            print(f"Edge TTS synthesis notice ({e}). Falling back to offline engine...")
            return self._synthesize_offline(text, preset, speed_mult, voice_name)

    def _synthesize_edge_tts(self, text: str, voice_id: str, rate_str: str, pitch_str: str) -> tuple[np.ndarray, int]:
        import time

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
            temp_path = tf.name

        try:
            for attempt in range(2):
                try:
                    captured_boundaries = []
                    audio_bytes = bytearray()

                    async def _run():
                        kwargs = {}
                        if rate_str and rate_str != "+0%":
                            kwargs["rate"] = rate_str
                        if pitch_str and pitch_str != "+0Hz":
                            kwargs["pitch"] = pitch_str
                        communicate = edge_tts.Communicate(
                            text=text,
                            voice=voice_id,
                            **kwargs
                        )
                        async for chunk in communicate.stream():
                            if chunk["type"] == "audio":
                                audio_bytes.extend(chunk["data"])
                            elif chunk["type"] == "SentenceBoundary":
                                start_sec = chunk.get("offset", 0) / 10_000_000.0
                                dur_sec = chunk.get("duration", 0) / 10_000_000.0
                                captured_boundaries.append({
                                    "text": chunk.get("text", ""),
                                    "start": start_sec,
                                    "end": start_sec + dur_sec
                                })

                    asyncio.run(_run())

                    if not audio_bytes:
                        raise RuntimeError("Empty audio output from TTS service.")

                    with open(temp_path, "wb") as f:
                        f.write(audio_bytes)

                    self.last_boundaries = captured_boundaries
                    data, sr = sf.read(temp_path)
                    if data.ndim > 1:
                        data = np.mean(data, axis=1)

                    return data.astype(np.float32), sr
                except Exception as err:
                    if attempt == 0:
                        time.sleep(0.6)
                        continue
                    raise err
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def _synthesize_offline(self, text: str, preset: dict, speed_mult: float, voice_name: str = "") -> tuple[np.ndarray, int]:
        """
        Synthesizes offline using Piper ONNX neural models (including distilled Abeo) if available,
        falling back to native Windows SAPI speech.
        """
        # 1. Try local Piper ONNX neural engine
        if self.offline_engine and self.offline_engine.is_ready():
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                temp_path = tf.name
            try:
                self.offline_engine.synthesize(text, temp_path, speed=speed_mult)
                data, sr = sf.read(temp_path)
                if data.ndim > 1:
                    data = np.mean(data, axis=1)
                return data.astype(np.float32), sr
            except Exception as e:
                print(f"[Offline] Piper ONNX notice ({e}), checking OS fallback...")
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

        # 2. Native Windows SAPI fallback if win32com is present
        try:
            import win32com.client
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                temp_path = tf.name

            try:
                sp = win32com.client.Dispatch("SAPI.SpVoice")
                target_gender = preset.get("offline_gender", "male").lower()
                voices = sp.GetVoices()
                for v in voices:
                    desc = v.GetDescription().lower()
                    if target_gender == "female" and ("zira" in desc or "female" in desc):
                        sp.Voice = v
                        break
                    elif target_gender == "male" and ("david" in desc or "male" in desc):
                        sp.Voice = v
                        break

                sapi_rate = int(round((speed_mult - 1.0) * 10))
                sp.Rate = max(-10, min(10, sapi_rate))

                stream = win32com.client.Dispatch("SAPI.SpFileStream")
                stream.Open(temp_path, 3, False)
                sp.AudioOutputStream = stream
                sp.Speak(text)
                stream.Close()

                data, sr = sf.read(temp_path)
                if data.ndim > 1:
                    data = np.mean(data, axis=1)
                return data.astype(np.float32), sr
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
        except Exception as e:
            raise RuntimeError(f"Offline speech synthesis unavailable (no Piper model or SAPI voice): {e}")


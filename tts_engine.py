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
    def synthesize(self, text: str, voice_name: str, speed_mult: float = 1.0, texture_val: int = 0) -> tuple[np.ndarray, int]:
        """
        Synthesizes text to speech.
        
        Args:
            text: Text to speak.
            voice_name: One of the 4 keys in VOICE_PRESETS.
            speed_mult: Speed factor (0.5 to 2.0). 1.0 is normal.
            texture_val: Texture / Pitch adjustment in Hz (-20 to +20).
                         Negative = deeper / warmer tone, Positive = crisp / bright tone.
                         
        Returns:
            (audio_numpy_array, sample_rate)
        """
        text = text.strip()
        if not text:
            raise ValueError("Input text is empty.")

        preset = VOICE_PRESETS.get(voice_name, VOICE_PRESETS["Deep Male"])
        voice_id = preset["id"]

        # Calculate rate string for edge-tts (e.g. "+15%", "-20%")
        rate_percent = int(round((speed_mult - 1.0) * 100))
        rate_str = f"{rate_percent:+d}%"

        # Calculate pitch string for edge-tts (base preset offset + user slider)
        total_pitch_hz = int(preset["base_pitch_offset"] + texture_val)
        pitch_str = f"{total_pitch_hz:+d}Hz"

        try:
            return self._synthesize_edge_tts(text, voice_id, rate_str, pitch_str)
        except Exception as e:
            print(f"Edge TTS synthesis notice ({e}). Falling back to offline Windows engine...")
            return self._synthesize_offline(text, preset, speed_mult)

    def _synthesize_edge_tts(self, text: str, voice_id: str, rate_str: str, pitch_str: str) -> tuple[np.ndarray, int]:
        import time

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
            temp_path = tf.name

        try:
            for attempt in range(2):
                try:
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
                        await communicate.save(temp_path)

                    asyncio.run(_run())

                    if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                        raise RuntimeError("Empty audio output from TTS service.")

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

    def _synthesize_offline(self, text: str, preset: dict, speed_mult: float) -> tuple[np.ndarray, int]:
        """
        Native Windows SAPI speech synthesis via win32com COM interface.
        Ultra-fast, zero-network, and never deadlocks.
        """
        import win32com.client

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            temp_path = tf.name

        try:
            sp = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Select gender
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

            # Rate: SAPI Rate is integer from -10 to +10 (0 is normal)
            # speed_mult 1.0 -> 0; 0.5 -> -5; 2.0 -> +7
            sapi_rate = int(round((speed_mult - 1.0) * 10))
            sp.Rate = max(-10, min(10, sapi_rate))

            # Stream to file
            stream = win32com.client.Dispatch("SAPI.SpFileStream")
            # 3 = SSFMCreateForWrite (overwrite if exists)
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


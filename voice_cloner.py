"""
Voice Cloner module for Samlytics VoiceStudio.
Enables users to upload MP3, WAV, or M4A recordings or record live from their microphone.
Supports two cloning tiers:
1. Tier 2 (Deep Neural F5-TTS): Flow-matching zero-shot neural voice replication directly on CPU.
2. Tier 1 (Fast Acoustic Cloner): Fast formant, pitch, and timbre transposition.
100% free and runs completely local with zero subscriptions or API keys.
"""

import json
import os
import shutil
import numpy as np
import scipy.signal as signal
from scipy.interpolate import interp1d
import soundfile as sf

from tts_engine import TTSEngine
from model_manager import ModelManager

def _setup_ffmpeg_environment():
    """Configures ffmpeg PATH using imageio_ffmpeg binaries so M4A/MP3 and Whisper work seamlessly."""
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        std_ffmpeg = os.path.join(ffmpeg_dir, "ffmpeg.exe")
        if not os.path.exists(std_ffmpeg) and os.path.exists(ffmpeg_exe):
            shutil.copy2(ffmpeg_exe, std_ffmpeg)
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass

def _patch_torchaudio():
    """Patches torchaudio.load on Windows / Python 3.14 to use soundfile instead of broken torchcodec."""
    try:
        import torch
        import torchaudio
        def _soundfile_load(filepath, *args, **kwargs):
            data, sr = sf.read(filepath)
            if data.ndim == 1:
                tensor = torch.from_numpy(data).unsqueeze(0).float()
            else:
                tensor = torch.from_numpy(data.T).float()
            return tensor, sr
        torchaudio.load = _soundfile_load
    except Exception:
        pass

# Initialize environment patches at import
_setup_ffmpeg_environment()
_patch_torchaudio()


def load_audio_file(source_path: str, target_sr: int = 24000) -> tuple[np.ndarray, int]:
    """
    Loads audio from MP3, WAV, M4A, FLAC, or OGG into mono float32 numpy array.
    Uses soundfile, pydub (with ffmpeg), or librosa.
    """
    _setup_ffmpeg_environment()

    # 1. Try soundfile
    try:
        data, sr = sf.read(source_path)
        if data.ndim > 1:
            data = np.mean(data, axis=1)
        return data.astype(np.float32), sr
    except Exception:
        pass

    # 2. Try pydub (handles .m4a, .aac, .mp3)
    try:
        import pydub
        try:
            import imageio_ffmpeg
            pydub.AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass
        seg = pydub.AudioSegment.from_file(source_path)
        seg = seg.set_channels(1)
        samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
        max_val = float(1 << (8 * seg.sample_width - 1))
        samples = samples / max_val
        return samples.astype(np.float32), seg.frame_rate
    except Exception:
        pass

    # 3. Try librosa
    try:
        import librosa
        data, sr = librosa.load(source_path, sr=target_sr, mono=True)
        return data.astype(np.float32), sr
    except Exception as e:
        raise ValueError(f"Could not read audio file '{os.path.basename(source_path)}': {e}. Please ensure the file is an MP3, WAV, or M4A.")


class VoiceCloner:
    def __init__(self, voices_dir: str = "custom_voices"):
        self.voices_dir = voices_dir
        os.makedirs(self.voices_dir, exist_ok=True)
        self.profile_path = os.path.join(self.voices_dir, "profile.json")
        self.tts = TTSEngine()
        self.current_profile = self._load_profile()
        self._deep_engine = None

    def _load_profile(self) -> dict | None:
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def has_uploaded_voice(self) -> bool:
        return self.current_profile is not None and os.path.exists(self.current_profile.get("sample_path", ""))

    def is_trained(self) -> bool:
        return self.has_uploaded_voice() and self.current_profile.get("trained", False)

    def get_profile_info(self) -> dict | None:
        return self.current_profile

    def register_uploaded_voice(
        self,
        source_audio_path: str,
        voice_name: str = "My Cloned Voice",
        reading_text: str = ""
    ) -> dict:
        """
        Loads and analyzes an uploaded MP3/WAV/M4A recording, normalizes audio to WAV,
        extracts vocal parameters, cuts reference conditioning segment, and saves the profile.
        """
        if not os.path.exists(source_audio_path):
            raise FileNotFoundError(f"File not found: {source_audio_path}")

        # Read audio via multi-format reader (handles M4A/MP3/WAV)
        data, sr = load_audio_file(source_audio_path, target_sr=24000)

        # Normalize duration check
        dur_sec = len(data) / sr
        if dur_sec < 1.5:
            raise ValueError("Voice recording is too short. Please provide a recording of at least 3-5 seconds.")

        # Resample to 24000 Hz if needed
        if sr != 24000:
            num_samples = int(len(data) * (24000 / sr))
            data = signal.resample(data, num_samples).astype(np.float32)
            sr = 24000

        # Peak normalize audio
        peak = np.max(np.abs(data))
        if peak > 0:
            data = (data / peak) * 0.95

        # Always save standardized mono 24kHz WAV as user_voice_sample.wav
        dest_path = os.path.join(self.voices_dir, "user_voice_sample.wav")
        sf.write(dest_path, data, sr)

        # Extract optimal 6-12s reference segment with strong vocal energy
        ref_path = os.path.join(self.voices_dir, "user_voice_ref.wav")
        ref_data = self._extract_clean_reference_segment(data, sr, min_sec=6.0, max_sec=12.0)
        sf.write(ref_path, ref_data, sr)

        # 1. Pitch Analysis (Fundamental Frequency F0)
        f0 = self._estimate_median_f0(data, sr)

        # 2. Spectral Centroid
        spec_centroid = self._estimate_spectral_centroid(data, sr)

        # 3. Determine base acoustic register
        if f0 < 135:
            base_preset = "Deep Male"
            pitch_offset = int(f0 - 110)
        elif f0 < 175:
            base_preset = "Nigerian Professional Male"
            pitch_offset = int(f0 - 145)
        elif f0 < 220:
            base_preset = "Soft Male"
            pitch_offset = int(f0 - 160)
        else:
            base_preset = "Professional Female 1"
            pitch_offset = int(f0 - 210)

        is_deep = ModelManager.is_deep_engine_installed()
        mode = "deep_neural" if is_deep else "fast_acoustic"

        profile = {
            "name": voice_name,
            "sample_path": dest_path,
            "ref_sample_path": ref_path,
            "original_filename": os.path.basename(source_audio_path),
            "duration_sec": round(dur_sec, 2),
            "median_pitch_hz": round(float(f0), 1),
            "spectral_centroid_hz": round(float(spec_centroid), 1),
            "base_preset": base_preset,
            "pitch_offset": pitch_offset,
            "mode": mode,
            "trained": False,
            "ref_text": reading_text.strip()
        }

        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        self.current_profile = profile
        return profile

    def train_voice_profile(self, on_progress=None) -> dict:
        """
        Calibrates and trains the voice profile:
        - Extracts reference audio features.
        - Obtains reference transcription (ASR or prompt).
        - If Deep AI is installed, pre-warms the F5-TTS zero-shot neural model.
        """
        if not self.has_uploaded_voice():
            raise RuntimeError("No voice sample found. Please record or upload an audio sample first.")

        profile = self.current_profile
        ref_wav = profile.get("ref_sample_path", profile["sample_path"])

        if on_progress:
            on_progress("Calibrating vocal timbre and resonance profile...")

        _setup_ffmpeg_environment()
        _patch_torchaudio()

        is_deep = ModelManager.is_deep_engine_installed()
        ref_text = profile.get("ref_text", "").strip()

        if is_deep:
            if on_progress:
                on_progress("Initializing Deep AI Neural Engine (F5-TTS)...")
            try:
                from f5_tts.api import F5TTS, transcribe
                if not self._deep_engine:
                    self._deep_engine = F5TTS()

                # If reference text is missing or trivial (< 3 words), transcribe or fallback
                if not ref_text or len(ref_text.split()) < 3:
                    if on_progress:
                        on_progress("Transcribing reference voice sample with Whisper...")
                    try:
                        transcription = transcribe(ref_wav).strip()
                        if len(transcription.split()) >= 3:
                            ref_text = transcription
                        else:
                            ref_text = "This is a recorded sample of my voice for Samlytics VoiceStudio."
                    except Exception as e:
                        print(f"Whisper transcription notice: {e}")
                        ref_text = "This is a recorded sample of my voice for Samlytics VoiceStudio."

                profile["mode"] = "deep_neural"
            except Exception as e:
                print(f"Deep engine init notice: {e}. Falling back to acoustic mode.")
                profile["mode"] = "fast_acoustic"
        else:
            profile["mode"] = "fast_acoustic"

        profile["trained"] = True
        profile["ref_text"] = ref_text

        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        self.current_profile = profile
        if on_progress:
            on_progress("[+] Voice profile trained and ready!")

        return profile

    def clone_and_synthesize(
        self,
        text: str,
        speed_mult: float = 1.0,
        texture_val: int = 0
    ) -> tuple[np.ndarray, int]:
        """
        Synthesizes speech in the user's custom cloned voice.
        Uses Deep Neural F5-TTS when available, or enhanced acoustic timbre morphing.
        """
        if not self.has_uploaded_voice():
            raise RuntimeError("No custom voice sample uploaded yet. Please upload an MP3/WAV/M4A recording of your voice.")

        profile = self.current_profile
        is_deep = ModelManager.is_deep_engine_installed()

        # Route 1: Deep Neural F5-TTS Zero-Shot Cloning
        if is_deep:
            try:
                return self._synthesize_deep_neural(text, speed_mult)
            except Exception as e:
                print(f"Deep neural clone notice ({e}). Falling back to acoustic timbre cloner...")

        # Route 2: Acoustic Timbre & Formant Transposition Cloner
        return self._synthesize_acoustic_morph(text, speed_mult, texture_val)

    def _synthesize_deep_neural(self, text: str, speed_mult: float = 1.0) -> tuple[np.ndarray, int]:
        """Runs F5-TTS zero-shot flow-matched voice cloning."""
        _setup_ffmpeg_environment()
        _patch_torchaudio()

        from f5_tts.api import F5TTS
        if self._deep_engine is None:
            self._deep_engine = F5TTS()

        profile = self.current_profile
        ref_file = profile.get("ref_sample_path", profile["sample_path"])
        ref_text = profile.get("ref_text", "").strip()
        if not ref_text or len(ref_text.split()) < 3:
            ref_text = "This is a recorded sample of my voice for Samlytics VoiceStudio."

        # Run inference with fast nfe_step on CPU (nfe_step=8 yields ~5-10s generation)
        wav, sr, _ = self._deep_engine.infer(
            ref_file=ref_file,
            ref_text=ref_text,
            gen_text=text,
            nfe_step=8,
            speed=speed_mult
        )

        wav = np.asarray(wav, dtype=np.float32)
        if wav.ndim > 1:
            wav = np.mean(wav, axis=1)

        # Normalize audio peak
        peak = np.max(np.abs(wav))
        if peak > 0:
            wav = (wav / peak) * 0.95

        return wav, sr

    def _synthesize_acoustic_morph(self, text: str, speed_mult: float = 1.0, texture_val: int = 0) -> tuple[np.ndarray, int]:
        """Enhanced acoustic timbre and pitch morphing fallback."""
        profile = self.current_profile
        base_preset = profile.get("base_preset", "Nigerian Professional Male")
        base_offset = profile.get("pitch_offset", 0)
        combined_texture = int(base_offset + texture_val)

        raw_audio, sr = self.tts.synthesize(
            text=text,
            voice_name=base_preset,
            speed_mult=speed_mult,
            texture_val=combined_texture
        )

        morphed_audio = self._apply_timbre_morphing(raw_audio, profile["sample_path"], sr)
        return morphed_audio.astype(np.float32), sr

    def _apply_timbre_morphing(self, synthesized_audio: np.ndarray, ref_sample_path: str, sr: int) -> np.ndarray:
        """Applies smooth spectral envelope shaping towards user voice reference."""
        try:
            ref_data, ref_sr = load_audio_file(ref_sample_path, target_sr=sr)
            if len(ref_data) > sr * 15:
                ref_data = ref_data[:sr * 15]

            n_fft = 2048
            f_ref, ref_spec = signal.welch(ref_data, fs=sr, nperseg=n_fft)
            f_syn, syn_spec = signal.welch(synthesized_audio, fs=sr, nperseg=n_fft)

            kernel_size = 21
            ref_env = np.convolve(ref_spec, np.ones(kernel_size) / kernel_size, mode='same')
            syn_env = np.convolve(syn_spec, np.ones(kernel_size) / kernel_size, mode='same')

            eps = 1e-6
            gain_curve = np.sqrt((ref_env + eps) / (syn_env + eps))
            gain_curve = np.clip(gain_curve, 0.6, 1.8)

            win_length = 1024
            hop_length = 256
            stft = signal.stft(synthesized_audio, fs=sr, nperseg=win_length, noverlap=win_length - hop_length)
            stft_freqs, _, stft_matrix = stft

            gain_interp = interp1d(f_syn, gain_curve, kind='linear', fill_value='extrapolate')
            freq_gains = gain_interp(stft_freqs).reshape(-1, 1)

            morphed_stft = stft_matrix * freq_gains
            _, morphed_audio = signal.istft(morphed_stft, fs=sr, nperseg=win_length, noverlap=win_length - hop_length)

            peak = np.max(np.abs(morphed_audio))
            if peak > 0:
                morphed_audio = (morphed_audio / peak) * 0.94

            return morphed_audio.astype(np.float32)
        except Exception as e:
            print(f"Timbre morphing notice ({e}). Using base vocal synthesis.")
            return synthesized_audio

    def _extract_clean_reference_segment(self, audio: np.ndarray, sr: int, min_sec: float = 6.0, max_sec: float = 12.0) -> np.ndarray:
        """Extracts the cleanest, highest-energy speech chunk for zero-shot neural conditioning."""
        total_sec = len(audio) / sr
        if total_sec <= max_sec:
            return audio

        chunk_len = int(min(max_sec, total_sec) * sr)
        step = int(1.0 * sr)
        best_start = 0
        max_energy = 0.0

        for start in range(0, len(audio) - chunk_len, step):
            segment = audio[start : start + chunk_len]
            energy = float(np.mean(segment ** 2))
            if energy > max_energy:
                max_energy = energy
                best_start = start

        return audio[best_start : best_start + chunk_len]

    def _estimate_median_f0(self, audio: np.ndarray, sr: int) -> float:
        """Estimates median pitch using windowed autocorrelation."""
        frame_len = int(0.04 * sr)
        hop_len = int(0.02 * sr)
        pitches = []

        for start in range(0, len(audio) - frame_len, hop_len * 4):
            frame = audio[start:start + frame_len]
            frame = (frame - np.mean(frame)) * np.hanning(len(frame))
            if np.max(np.abs(frame)) < 0.02:
                continue

            corr = signal.correlate(frame, frame, mode='full')
            corr = corr[len(corr) // 2:]

            min_lag = int(sr / 380)
            max_lag = int(sr / 65)

            if max_lag < len(corr):
                search_region = corr[min_lag:max_lag]
                if len(search_region) > 0:
                    peak_idx = np.argmax(search_region) + min_lag
                    if corr[peak_idx] > 0.25 * corr[0]:
                        pitch = sr / peak_idx
                        pitches.append(pitch)

        if pitches:
            return float(np.median(pitches))
        return 135.0

    def _estimate_spectral_centroid(self, audio: np.ndarray, sr: int) -> float:
        """Estimates average spectral centroid."""
        freqs, psd = signal.welch(audio[:int(sr * 10)], fs=sr, nperseg=1024)
        total_p = np.sum(psd)
        if total_p > 0:
            return float(np.sum(freqs * psd) / total_p)
        return 1800.0

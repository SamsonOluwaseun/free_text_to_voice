"""
Audio Mixer module.
Handles:
- Loading and listing background instrumental tracks
- Importing external music tracks
- Sample rate alignment and looping
- Smart storytelling audio ducking (dipping music when speech is active)
- Gain control for both voice and music
- MP3 and WAV high-fidelity export
"""

import os
import shutil
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from math import gcd

class AudioMixer:
    def __init__(self, tracks_dir: str = "background_tracks"):
        self.tracks_dir = tracks_dir
        os.makedirs(self.tracks_dir, exist_ok=True)

    def get_available_tracks(self) -> dict[str, str]:
        """
        Returns a dictionary mapping display names to relative file paths.
        Includes a 'None (Speech Only)' option.
        """
        tracks = {"None (Voice Only)": ""}
        valid_exts = {".wav", ".mp3", ".ogg", ".flac"}
        
        if os.path.exists(self.tracks_dir):
            files = sorted(os.listdir(self.tracks_dir))
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in valid_exts:
                    # Create clean display name
                    clean_name = os.path.splitext(f)[0]
                    # Strip leading track number if present (e.g. '01_')
                    parts = clean_name.split("_", 1)
                    if len(parts) == 2 and parts[0].isdigit():
                        display_name = parts[1].replace("_", " ").title()
                    else:
                        display_name = clean_name.replace("_", " ").title()
                    full_path = os.path.join(self.tracks_dir, f)
                    tracks[display_name] = full_path
                    
        return tracks

    def import_track(self, source_path: str) -> str:
        """
        Copies an external audio file into the background_tracks directory.
        Returns the destination file path.
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"File not found: {source_path}")
        
        base_name = os.path.basename(source_path)
        dest_path = os.path.join(self.tracks_dir, base_name)
        
        # Avoid duplicate name collision
        if os.path.exists(dest_path):
            name, ext = os.path.splitext(base_name)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(self.tracks_dir, f"{name}_{counter}{ext}")
                counter += 1
                
        shutil.copy2(source_path, dest_path)
        return dest_path

    def mix_audio(
        self,
        voice_data: np.ndarray,
        sr: int,
        bg_track_path: str = "",
        voice_volume: float = 1.0,
        bg_volume: float = 0.25,
        ducking: bool = True
    ) -> tuple[np.ndarray, int]:
        """
        Mixes speech audio with optional background instrumental music.
        
        Args:
            voice_data: 1D or 2D numpy array of voice samples.
            sr: Sample rate of the voice audio.
            bg_track_path: Path to background audio file (or empty for voice only).
            voice_volume: Multiplier for voice (0.0 to 1.5).
            bg_volume: Multiplier for background music (0.0 to 1.0).
            ducking: Whether to automatically lower music volume during speech.
            
        Returns:
            (mixed_audio_array, sr)
        """
        # Ensure 1D mono for base calculations
        if voice_data.ndim > 1:
            voice_data = np.mean(voice_data, axis=1)
            
        # Apply voice volume
        voice_scaled = voice_data * voice_volume
        
        # If no background track is selected or volume is zero, return voice
        if not bg_track_path or not os.path.exists(bg_track_path) or bg_volume <= 0.001:
            max_v = np.max(np.abs(voice_scaled))
            if max_v > 0.98:
                voice_scaled = (voice_scaled / max_v) * 0.95
            return voice_scaled.astype(np.float32), sr

        # Load background music
        bg_data, bg_sr = sf.read(bg_track_path)
        if bg_data.ndim > 1:
            bg_data = np.mean(bg_data, axis=1)

        # Resample music if sample rates differ
        if bg_sr != sr:
            d = gcd(sr, bg_sr)
            up = sr // d
            down = bg_sr // d
            bg_data = resample_poly(bg_data, up, down)

        # Allow 1.5s outro tail for music to resolve naturally
        outro_tail_len = int(1.5 * sr)
        total_len = len(voice_scaled) + outro_tail_len

        # Loop background track to fit total length
        bg_loop = np.zeros(total_len, dtype=np.float32)
        bg_len = len(bg_data)
        if bg_len > 0:
            for offset in range(0, total_len, bg_len):
                chunk = min(bg_len, total_len - offset)
                bg_loop[offset:offset + chunk] = bg_data[:chunk]

        # Calculate ducking envelope
        bg_gain = np.ones(total_len, dtype=np.float32) * bg_volume
        if ducking and len(voice_scaled) > 0:
            # Voice energy tracking with a moving window
            window_size = int(0.15 * sr)  # 150ms window
            voice_padded = np.zeros(total_len)
            voice_padded[:len(voice_scaled)] = voice_scaled
            
            # Simple envelope follower
            abs_voice = np.abs(voice_padded)
            # Smooth envelope
            smooth_kernel = np.ones(window_size) / window_size
            env = np.convolve(abs_voice, smooth_kernel, mode='same')
            
            threshold = 0.03
            # Ducking factor: lower background music by ~55% when speaking
            duck_reduction = 0.45
            duck_mask = np.clip((env - threshold) / (threshold * 3), 0.0, 1.0)
            duck_mult = 1.0 - (duck_mask * (1.0 - duck_reduction))
            bg_gain = bg_gain * duck_mult

        # Apply gain to background music
        bg_scaled = bg_loop * bg_gain

        # Apply smooth fade in (1.0s) and fade out (1.8s) on background music
        fade_in_len = min(int(1.0 * sr), total_len // 4)
        fade_out_len = min(int(1.8 * sr), total_len // 3)
        if fade_in_len > 0:
            bg_scaled[:fade_in_len] *= np.linspace(0.0, 1.0, fade_in_len)
        if fade_out_len > 0:
            bg_scaled[-fade_out_len:] *= np.linspace(1.0, 0.0, fade_out_len)

        # Pad voice to match total length
        voice_out = np.zeros(total_len, dtype=np.float32)
        voice_out[:len(voice_scaled)] = voice_scaled

        # Mix signals
        mixed = voice_out + bg_scaled

        # Peak normalization & soft-clipping protection
        peak = np.max(np.abs(mixed))
        if peak > 0.95:
            # Soft limiting
            mixed = np.tanh(mixed / peak) * 0.95
        else:
            mixed = mixed * 0.95

        return mixed.astype(np.float32), sr

    @staticmethod
    def export_audio(audio_data: np.ndarray, sr: int, output_filepath: str):
        """
        Exports audio array to either MP3 or WAV based on file extension.
        """
        ext = os.path.splitext(output_filepath)[1].lower()
        if ext == ".mp3":
            sf.write(output_filepath, audio_data, sr, format='MP3')
        elif ext in [".wav", ""]:
            if not output_filepath.endswith(".wav"):
                output_filepath += ".wav"
            sf.write(output_filepath, audio_data, sr, format='WAV', subtype='PCM_16')
        else:
            # Fallback
            sf.write(output_filepath, audio_data, sr)


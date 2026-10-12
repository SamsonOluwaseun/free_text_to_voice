"""
Live Microphone Audio Recorder.
Allows users to record their voice directly within Samlytics VoiceStudio
for custom voice cloning, without needing third-party recording tools.
Uses sounddevice.InputStream for low-latency, thread-safe capture.
"""

import threading
import time
import numpy as np
import sounddevice as sd
import soundfile as sf

class AudioRecorder:
    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate
        self.is_recording = False
        self.frames = []
        self.stream = None
        self.start_time = 0.0
        self.lock = threading.Lock()

    def get_input_device(self):
        """Finds the default or first valid microphone input device."""
        try:
            default_in = sd.default.device[0]
            if default_in is not None and default_in >= 0:
                return default_in
            # Search available input devices
            for idx, dev in enumerate(sd.query_devices()):
                if dev.get('max_input_channels', 0) > 0:
                    return idx
        except Exception:
            pass
        return None

    def _audio_callback(self, indata, frames, time_info, status):
        with self.lock:
            if self.is_recording:
                self.frames.append(indata.copy())

    def start_recording(self):
        """Starts capturing audio from the microphone."""
        if self.is_recording:
            return

        with self.lock:
            self.frames = []
            self.is_recording = True
            self.start_time = time.time()

        device = self.get_input_device()
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            device=device,
            callback=self._audio_callback
        )
        self.stream.start()

    def stop_recording(self, output_filepath: str) -> tuple[np.ndarray, float]:
        """
        Stops recording and saves the captured audio to output_filepath.
        Returns: (audio_data, duration_seconds)
        """
        if not self.is_recording:
            raise RuntimeError("Recorder is not active.")

        with self.lock:
            self.is_recording = False

        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        with self.lock:
            if not self.frames:
                raise RuntimeError("No audio frames were captured from your microphone.")
            audio_data = np.concatenate(self.frames, axis=0)

        # Ensure 1D array
        if audio_data.ndim > 1:
            audio_data = audio_data.flatten()

        duration = len(audio_data) / self.sample_rate

        # Normalize and save
        peak = np.max(np.abs(audio_data))
        if peak > 0:
            audio_data = (audio_data / peak) * 0.90

        sf.write(output_filepath, audio_data, self.sample_rate, subtype='PCM_16')
        return audio_data, duration

    def get_elapsed_seconds(self) -> float:
        """Returns current recording duration in seconds."""
        if not self.is_recording:
            return 0.0
        return max(0.0, time.time() - self.start_time)

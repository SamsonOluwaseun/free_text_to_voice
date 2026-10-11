"""
Audio Player module using sounddevice.
Provides thread-safe Play, Pause, Resume, Stop, Seek, and position tracking
for seamless preview in the GUI.
"""

import threading
import time
import numpy as np
import sounddevice as sd

class AudioPlayer:
    def __init__(self, on_finish_callback=None):
        self.audio_data = None
        self.sr = 24000
        self.stream = None
        self.is_playing = False
        self.is_paused = False
        self.current_frame = 0
        self.total_frames = 0
        self.lock = threading.Lock()
        self.on_finish_callback = on_finish_callback

    def load(self, audio_data: np.ndarray, sr: int):
        """Loads new audio data into the player and resets position."""
        self.stop()
        with self.lock:
            # Ensure float32 and 2D array (frames, channels) for sounddevice
            if audio_data.ndim == 1:
                self.audio_data = audio_data.reshape(-1, 1).astype(np.float32)
            else:
                self.audio_data = audio_data.astype(np.float32)
            self.sr = sr
            self.current_frame = 0
            self.total_frames = len(self.audio_data)

    def _audio_callback(self, outdata, frames, time_info, status):
        with self.lock:
            if not self.is_playing or self.is_paused or self.audio_data is None:
                outdata.fill(0)
                return

            remaining_frames = self.total_frames - self.current_frame
            if remaining_frames <= 0:
                outdata.fill(0)
                self.is_playing = False
                self.current_frame = 0
                if self.on_finish_callback:
                    threading.Thread(target=self.on_finish_callback, daemon=True).start()
                raise sd.CallbackStop()

            chunk_size = min(frames, remaining_frames)
            outdata[:chunk_size] = self.audio_data[self.current_frame : self.current_frame + chunk_size]
            if chunk_size < frames:
                outdata[chunk_size:].fill(0)

            self.current_frame += chunk_size

    def play(self):
        """Starts or resumes playback."""
        with self.lock:
            if self.audio_data is None or self.total_frames == 0:
                return

            if self.is_paused and self.stream and self.stream.active:
                self.is_paused = False
                self.is_playing = True
                return

            self._close_stream()
            self.is_playing = True
            self.is_paused = False

            channels = self.audio_data.shape[1]
            self.stream = sd.OutputStream(
                samplerate=self.sr,
                channels=channels,
                dtype='float32',
                callback=self._audio_callback
            )
            self.stream.start()

    def pause(self):
        """Pauses current playback."""
        with self.lock:
            if self.is_playing:
                self.is_paused = True
                self.is_playing = False

    def stop(self):
        """Stops playback and resets to beginning."""
        with self.lock:
            self.is_playing = False
            self.is_paused = False
            self.current_frame = 0
            self._close_stream()

    def seek(self, target_seconds: float):
        """Seeks to the given timestamp in seconds."""
        with self.lock:
            if self.total_frames == 0:
                return
            target_frame = int(target_seconds * self.sr)
            self.current_frame = max(0, min(target_frame, self.total_frames))

    def get_position(self) -> float:
        """Returns current playback position in seconds."""
        with self.lock:
            if self.sr <= 0:
                return 0.0
            return self.current_frame / self.sr

    def get_duration(self) -> float:
        """Returns total audio duration in seconds."""
        with self.lock:
            if self.total_frames == 0 or self.sr <= 0:
                return 0.0
            return self.total_frames / self.sr

    def _close_stream(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None


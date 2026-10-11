"""
Procedural ambient and storytelling instrumental generator.
Generates 10 high-quality royalty-free ambient instrumental tracks
using mathematical acoustic synthesis, warm harmonic chords,
and spatial filtering.
"""

import os
import numpy as np
import soundfile as sf
from scipy.signal import butter, filtfilt

SAMPLE_RATE = 24000
DURATION_SEC = 25  # 25 seconds per track, auto-looped in mixer if story is longer

def lowpass_filter(data, cutoff, sr=SAMPLE_RATE, order=3):
    nyq = 0.5 * sr
    norm_cutoff = min(cutoff / nyq, 0.99)
    b, a = butter(order, norm_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data)

def highpass_filter(data, cutoff, sr=SAMPLE_RATE, order=3):
    nyq = 0.5 * sr
    norm_cutoff = min(cutoff / nyq, 0.99)
    b, a = butter(order, norm_cutoff, btype='high', analog=False)
    return filtfilt(b, a, data)

def normalize(audio, peak=0.75):
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        return (audio / max_val) * peak
    return audio

def apply_fade(audio, fade_in_sec=1.5, fade_out_sec=2.0, sr=SAMPLE_RATE):
    fade_in_len = int(fade_in_sec * sr)
    fade_out_len = int(fade_out_sec * sr)
    audio = audio.copy()
    if len(audio) > fade_in_len:
        audio[:fade_in_len] *= np.linspace(0, 1, fade_in_len)
    if len(audio) > fade_out_len:
        audio[-fade_out_len:] *= np.linspace(1, 0, fade_out_len)
    return audio

def m_to_hz(midi_note):
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

def generate_piano_note(freq, duration, sr=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Fundamental + harmonics with exponential decay
    decay1 = np.exp(-t * 2.2)
    decay2 = np.exp(-t * 3.5)
    decay3 = np.exp(-t * 5.0)
    sig = (
        1.0 * np.sin(2 * np.pi * freq * t) * decay1 +
        0.5 * np.sin(2 * np.pi * 2 * freq * t) * decay2 +
        0.25 * np.sin(2 * np.pi * 3 * freq * t) * decay3 +
        0.1 * np.sin(2 * np.pi * 4 * freq * t) * np.exp(-t * 7.0)
    )
    return sig

def generate_pad_chord(frequencies, duration, sr=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    sig = np.zeros_like(t)
    for f in frequencies:
        # Detuned oscillators for lush chorus effect
        sig += 0.35 * np.sin(2 * np.pi * (f - 0.4) * t)
        sig += 0.35 * np.sin(2 * np.pi * f * t)
        sig += 0.35 * np.sin(2 * np.pi * (f + 0.4) * t)
        sig += 0.15 * np.sin(2 * np.pi * (2 * f) * t)
    # Slow gentle vibrato / tremolo
    sig *= (0.85 + 0.15 * np.sin(2 * np.pi * 0.25 * t))
    return lowpass_filter(sig, 800, sr)

# --- Track 1: Ethereal Ambient Piano ---
def track_ethereal_piano():
    sr = SAMPLE_RATE
    total_len = int(sr * DURATION_SEC)
    audio = np.zeros(total_len)
    # Progression: Cmaj7 -> Am9 -> Fmaj7 -> Gsus4
    chords = [
        ([48, 55, 59, 64], 6.0),
        ([45, 52, 57, 60], 6.0),
        ([41, 48, 53, 57], 6.0),
        ([43, 50, 55, 62], 7.0),
    ]
    cur_pos = 0
    for notes, chord_dur in chords:
        # Background warm pad
        pad = generate_pad_chord([m_to_hz(n) for n in notes], chord_dur, sr)
        p_len = min(len(pad), total_len - cur_pos)
        audio[cur_pos:cur_pos + p_len] += pad[:p_len] * 0.45
        
        # Arpeggiated delicate notes
        note_times = np.linspace(0, chord_dur - 1.2, len(notes) + 2)
        for i, n_t in enumerate(note_times):
            note_idx = notes[i % len(notes)] + (12 if i >= len(notes) else 0)
            note_audio = generate_piano_note(m_to_hz(note_idx), 3.0, sr)
            start_samp = cur_pos + int(n_t * sr)
            end_samp = min(start_samp + len(note_audio), total_len)
            if start_samp < total_len:
                audio[start_samp:end_samp] += note_audio[:end_samp - start_samp] * 0.6
                
        cur_pos += int(chord_dur * sr)
    return apply_fade(normalize(audio))

# --- Track 2: Lo-Fi Night Thoughts ---
def track_lofi_night():
    sr = SAMPLE_RATE
    total_len = int(sr * DURATION_SEC)
    t = np.linspace(0, DURATION_SEC, total_len, endpoint=False)
    # Lo-fi vinyl / warm tape hiss
    vinyl = np.random.normal(0, 0.03, total_len)
    vinyl = lowpass_filter(vinyl, 2500, sr)
    
    # Chill jazz chords: Dm9 -> G13 -> Cmaj9 -> A7b13
    chords = [
        ([50, 57, 60, 64, 69], 6.0),
        ([43, 53, 57, 59, 64], 6.0),
        ([48, 55, 59, 62, 67], 6.0),
        ([45, 53, 56, 61, 65], 7.0),
    ]
    music = np.zeros(total_len)
    cur = 0
    for chord, dur in chords:
        pad = generate_pad_chord([m_to_hz(n) for n in chord], dur, sr)
        p_len = min(len(pad), total_len - cur)
        music[cur:cur + p_len] += pad[:p_len] * 0.7
        cur += int(dur * sr)
        
    # Lo-fi subtle sub-bass pulse
    kick_pulse = np.zeros(total_len)
    beat_step = int(1.2 * sr)
    for b in range(0, total_len, beat_step):
        k_len = int(0.3 * sr)
        k_t = np.linspace(0, 0.3, k_len)
        k_wave = np.sin(2 * np.pi * 55 * np.exp(-k_t * 10) * k_t) * np.exp(-k_t * 8)
        end = min(b + k_len, total_len)
        kick_pulse[b:end] += k_wave[:end - b] * 0.35
        
    combined = music + vinyl + kick_pulse
    combined = lowpass_filter(combined, 1800, sr)
    return apply_fade(normalize(combined))

# --- Track 3: Cinematic Story Strings ---
def track_cinematic_strings():
    sr = SAMPLE_RATE
    total_len = int(sr * DURATION_SEC)
    audio = np.zeros(total_len)
    # Cinematic progression: Em -> C -> G -> D
    chords = [
        ([40, 47, 52, 55, 64], 6.0),
        ([36, 43, 48, 55, 60], 6.0),
        ([43, 47, 50, 55, 59], 6.0),
        ([38, 45, 50, 54, 62], 7.0),
    ]
    cur = 0
    t = np.linspace(0, DURATION_SEC, total_len, endpoint=False)
    for chord, dur in chords:
        pad = generate_pad_chord([m_to_hz(n) for n in chord], dur, sr)
        p_len = min(len(pad), total_len - cur)
        # Slow crescendo
        env = np.linspace(0.4, 0.85, p_len)
        audio[cur:cur + p_len] += (pad[:p_len] * env)
        cur += int(dur * sr)
    return apply_fade(normalize(audio))

# --- Track 4: Cozy Acoustic Warmth ---
def track_acoustic_warmth():
    sr = SAMPLE_RATE
    total_len = int(sr * DURATION_SEC)
    audio = np.zeros(total_len)
    # Acoustic warmth chords: D -> G -> Bm -> A
    chords = [
        ([50, 57, 62, 66], 6.0),
        ([43, 50, 55, 59], 6.0),
        ([47, 54, 59, 62], 6.0),
        ([45, 52, 57, 61], 7.0),
    ]
    cur = 0
    for chord, dur in chords:
        pad = generate_pad_chord([m_to_hz(n) for n in chord], dur, sr)
        p_len = min(len(pad), total_len - cur)
        audio[cur:cur + p_len] += pad[:p_len] * 0.4
        
        # Plucked guitar arpeggios
        for step in range(int(dur / 0.6)):
            idx = chord[step % len(chord)] + 12
            freq = m_to_hz(idx)
            pluck_dur = 1.8
            p_t = np.linspace(0, pluck_dur, int(sr * pluck_dur))
            pluck = (np.sin(2 * np.pi * freq * p_t) + 0.3 * np.sin(2 * np.pi * 2 * freq * p_t)) * np.exp(-p_t * 3.5)
            start_s = cur + int(step * 0.6 * sr)
            end_s = min(start_s + len(pluck), total_len)
            if start_s < total_len:
                audio[start_s:end_s] += pluck[:end_s - start_s] * 0.5
        cur += int(dur * sr)
    return apply_fade(normalize(audio))

# --- Track 5: Deep Space Ambient Drone ---
def track_space_ambient():
    sr = SAMPLE_RATE
    total_len = int(sr * DURATION_SEC)
    t = np.linspace(0, DURATION_SEC, total_len, endpoint=False)
    # Deep drone harmonics
    base = 55.0  # A1
    drone = (
        0.5 * np.sin(2 * np.pi * base * t) +
        0.35 * np.sin(2 * np.pi * (base * 1.5) * t) +
        0.25 * np.sin(2 * np.pi * (base * 2.0) * t) +
        0.15 * np.sin(2 * np.pi * (base * 3.0) * t)
    )
    # Swelling cosmic shimmer
    shimmer = np.sin(2 * np.pi * 0.15 * t) * np.sin(2 * np.pi * (base * 4.01) * t) * 0.2
    combined = lowpass_filter(drone + shimmer, 450, sr)
    return apply_fade(normalize(combined))

# --- Track 6: Gentle Fairytale Harp ---
def track_fairytale_harp():
    sr = SAMPLE_RATE
    total_len = int(sr * DURATION_SEC)
    audio = np.zeros(total_len)
    scale = [60, 62, 64, 67, 69, 72, 74, 76, 79, 81]  # Pentatonic major
    pad = generate_pad_chord([m_to_hz(n) for n in [48, 55, 60, 64]], DURATION_SEC, sr)
    audio += pad[:total_len] * 0.3
    
    # Cascading harp glissandos
    for t_step in np.arange(0.5, DURATION_SEC - 2.0, 3.2):
        for i in range(6):
            note = scale[(i * 2) % len(scale)]
            freq = m_to_hz(note)
            h_dur = 2.0
            h_t = np.linspace(0, h_dur, int(sr * h_dur))
            h_wave = np.sin(2 * np.pi * freq * h_t) * np.exp(-h_t * 2.8)
            start_s = int((t_step + i * 0.18) * sr)
            end_s = min(start_s + len(h_wave), total_len)
            if start_s < total_len:
                audio[start_s:end_s] += h_wave[:end_s - start_s] * 0.45
    return apply_fade(normalize(audio))

# --- Track 7: Nature & Gentle Rain ---
def track_nature_rain():
    sr = SAMPLE_RATE
    total_len = int(sr * DURATION_SEC)
    t = np.linspace(0, DURATION_SEC, total_len, endpoint=False)
    # Soft rain sound: bandpassed pink/brown noise
    noise = np.random.normal(0, 0.15, total_len)
    rain = lowpass_filter(highpass_filter(noise, 400, sr), 3200, sr)
    
    # Soft wind swells
    wind_env = (np.sin(2 * np.pi * 0.08 * t) ** 2) * 0.25
    wind = lowpass_filter(np.random.normal(0, 0.2, total_len), 300, sr) * wind_env
    
    # Distant warm rhodes chime chords
    ambient_chord = generate_pad_chord([m_to_hz(n) for n in [53, 57, 60, 65]], DURATION_SEC, sr)
    
    combined = rain * 0.5 + wind * 0.3 + ambient_chord * 0.25
    return apply_fade(normalize(combined))

# --- Track 8: Meditative Zen Singing Bowls ---
def track_zen_meditation():
    sr = SAMPLE_RATE
    total_len = int(sr * DURATION_SEC)
    audio = np.zeros(total_len)
    t = np.linspace(0, DURATION_SEC, total_len, endpoint=False)
    # Deep Om drone
    om_drone = (np.sin(2 * np.pi * 108 * t) + 0.3 * np.sin(2 * np.pi * 216 * t)) * 0.35
    om_drone = lowpass_filter(om_drone, 300, sr)
    audio += om_drone
    
    # Tibetan bell / singing bowl strikes
    bowl_freqs = [288, 384, 432, 576]
    for strike_idx, strike_time in enumerate([1.0, 7.5, 14.0, 20.0]):
        freq = bowl_freqs[strike_idx % len(bowl_freqs)]
        b_dur = 6.5
        b_t = np.linspace(0, b_dur, int(sr * b_dur))
        # Bell overtone formula
        bell = (
            np.sin(2 * np.pi * freq * b_t) * np.exp(-b_t * 0.6) +
            0.4 * np.sin(2 * np.pi * freq * 2.76 * b_t) * np.exp(-b_t * 1.2) +
            0.2 * np.sin(2 * np.pi * freq * 5.4 * b_t) * np.exp(-b_t * 2.0)
        )
        start_s = int(strike_time * sr)
        end_s = min(start_s + len(bell), total_len)
        if start_s < total_len:
            audio[start_s:end_s] += bell[:end_s - start_s] * 0.55
            
    return apply_fade(normalize(audio))

# --- Track 9: Mystery & Suspense Atmosphere ---
def track_mystery_suspense():
    sr = SAMPLE_RATE
    total_len = int(sr * DURATION_SEC)
    t = np.linspace(0, DURATION_SEC, total_len, endpoint=False)
    # Low tense cello drone in D minor
    freq = m_to_hz(38)  # D2
    cello = (
        0.5 * np.sin(2 * np.pi * freq * t) +
        0.3 * np.sin(2 * np.pi * (freq * 1.498) * t) + # Diminished / minor 5th tension
        0.2 * np.sin(2 * np.pi * (freq * 3.0) * t)
    )
    # Slow tremolo
    trem = 0.7 + 0.3 * np.sin(2 * np.pi * 4.5 * t)
    cello = cello * trem
    
    # Eerie glassy high bell ping
    ping_len = int(3.0 * sr)
    p_t = np.linspace(0, 3.0, ping_len)
    ping = (np.sin(2 * np.pi * 1760 * p_t) + np.sin(2 * np.pi * 1864 * p_t)) * np.exp(-p_t * 1.5) * 0.25
    
    for ping_t in [3.0, 11.0, 18.5]:
        s = int(ping_t * sr)
        e = min(s + ping_len, total_len)
        if s < total_len:
            cello[s:e] += ping[:e - s]
            
    combined = lowpass_filter(cello, 1100, sr)
    return apply_fade(normalize(combined))

# --- Track 10: Warm Sunrise Ambiance ---
def track_warm_sunrise():
    sr = SAMPLE_RATE
    total_len = int(sr * DURATION_SEC)
    # Progression: F# -> B -> D#m -> C# (Bright, hopeful)
    chords = [
        ([42, 49, 54, 58, 66], 6.0),
        ([47, 54, 59, 63, 66], 6.0),
        ([39, 51, 54, 63, 66], 6.0),
        ([49, 56, 61, 65, 68], 7.0),
    ]
    audio = np.zeros(total_len)
    cur = 0
    for chord, dur in chords:
        pad = generate_pad_chord([m_to_hz(n) for n in chord], dur, sr)
        p_len = min(len(pad), total_len - cur)
        audio[cur:cur + p_len] += pad[:p_len] * 0.65
        cur += int(dur * sr)
    return apply_fade(normalize(audio))

TRACKS = {
    "01_ethereal_piano.wav": ("Ethereal Piano", track_ethereal_piano),
    "02_lofi_night.wav": ("Lo-Fi Night Thoughts", track_lofi_night),
    "03_cinematic_strings.wav": ("Cinematic Story Strings", track_cinematic_strings),
    "04_acoustic_warmth.wav": ("Cozy Acoustic Warmth", track_acoustic_warmth),
    "05_space_ambient.wav": ("Deep Space Ambient", track_space_ambient),
    "06_fairytale_harp.wav": ("Gentle Fairytale Harp", track_fairytale_harp),
    "07_nature_rain.wav": ("Nature & Gentle Rain", track_nature_rain),
    "08_zen_meditation.wav": ("Meditative Zen Bells", track_zen_meditation),
    "09_mystery_suspense.wav": ("Mystery & Suspense", track_mystery_suspense),
    "10_warm_sunrise.wav": ("Warm Sunrise Hope", track_warm_sunrise),
}

def ensure_starter_tracks(target_dir="background_tracks"):
    os.makedirs(target_dir, exist_ok=True)
    generated = []
    for filename, (title, func) in TRACKS.items():
        file_path = os.path.join(target_dir, filename)
        if not os.path.exists(file_path):
            print(f"Generating instrumental: {title} -> {filename}...")
            data = func()
            sf.write(file_path, data, SAMPLE_RATE)
            generated.append(file_path)
    return generated

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "background_tracks")
    ensure_starter_tracks(out_dir)
    print("All 10 starter instrumentals ready!")


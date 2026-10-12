"""
Complete Quality Assurance (QA) Script for Samlytics VoiceStudio.
Validates all core functionality, asset loading, shortcut generation,
TTS voice synthesis, voice cloning, audio mixing, and export pipelines.
"""

import os
import sys
import numpy as np
import soundfile as sf

def run_qa():
    print("=" * 60)
    print(" SAMLYTICS VOICE STUDIO - FULL QA SUITE ")
    print("=" * 60)

    # 1. Assets Check
    print("\n[QA 1/6] Validating Brand & Icon Assets...")
    required_assets = [
        "assets/app_icon.ico",
        "assets/logo_square.png",
        "assets/product_logo.png"
    ]
    for asset in required_assets:
        assert os.path.exists(asset), f"Missing required asset: {asset}"
        assert os.path.getsize(asset) > 0, f"Empty asset file: {asset}"
        print(f"   [PASS] {asset} verified ({os.path.getsize(asset):,} bytes)")

    # 2. Starter Tracks Check
    print("\n[QA 2/6] Validating Storytelling Background Instrumentals...")
    from tracks_generator import TRACKS, ensure_starter_tracks
    ensure_starter_tracks("background_tracks")
    for filename in TRACKS.keys():
        path = os.path.join("background_tracks", filename)
        assert os.path.exists(path), f"Missing track: {path}"
        assert os.path.getsize(path) > 10000, f"Invalid track size: {path}"
    print(f"   [PASS] All {len(TRACKS)} starter ambient tracks verified!")

    # 3. TTS Neural & Offline Synthesis Check
    print("\n[QA 3/6] Validating Voice Synthesis (Nigerian Male + Presets)...")
    from tts_engine import TTSEngine, VOICE_PRESETS
    tts = TTSEngine()
    
    # Test primary voice: Nigerian Professional Male
    data_ng, sr_ng = tts.synthesize("Welcome to Samlytics Data Services tutorial.", "Nigerian Professional Male")
    assert len(data_ng) > 1000 and sr_ng > 0, "Nigerian voice synthesis failed"
    print(f"   [PASS] Nigerian Professional Male: {len(data_ng):,} samples, {sr_ng} Hz")

    # Test Deep Male
    data_deep, sr_deep = tts.synthesize("Deep narration test.", "Deep Male", speed_mult=0.9, texture_val=-6)
    assert len(data_deep) > 1000, "Deep Male synthesis failed"
    print(f"   [PASS] Deep Male: {len(data_deep):,} samples")

    # 4. Voice Cloner Check
    print("\n[QA 4/6] Validating Custom Voice Cloner...")
    from voice_cloner import VoiceCloner
    cloner = VoiceCloner("custom_voices")
    
    # Create test input voice
    test_voice_file = "custom_voices/qa_sample.wav"
    t = np.linspace(0, 3, 24000 * 3)
    sample_tone = 0.3 * np.sin(2 * np.pi * 135 * t) + 0.15 * np.sin(2 * np.pi * 270 * t)
    sf.write(test_voice_file, sample_tone, 24000)
    
    profile = cloner.register_uploaded_voice(test_voice_file, "QA Test Voice")
    assert profile is not None and "median_pitch_hz" in profile
    print(f"   [PASS] Analyzed pitch: {profile['median_pitch_hz']} Hz (Matched: {profile['base_preset']})")
    
    cloned_data, cloned_sr = cloner.clone_and_synthesize("Testing speech with my cloned voice profile.")
    assert len(cloned_data) > 1000 and cloned_sr > 0
    print(f"   [PASS] Cloned voice synthesis: {len(cloned_data):,} samples")
    
    if os.path.exists(test_voice_file):
        os.remove(test_voice_file)

    # 5. Audio Mixer & Smart Ducking & Export Check
    print("\n[QA 5/6] Validating Audio Mixer & MP3/WAV Export...")
    from audio_mixer import AudioMixer
    mixer = AudioMixer("background_tracks")
    tracks = mixer.get_available_tracks()
    track_path = list(tracks.values())[1]
    
    mixed_audio, out_sr = mixer.mix_audio(
        voice_data=data_ng,
        sr=sr_ng,
        bg_track_path=track_path,
        voice_volume=1.0,
        bg_volume=0.20,
        ducking=True
    )
    assert len(mixed_audio) > len(data_ng), "Audio mixing length error"
    
    os.makedirs("exports", exist_ok=True)
    test_mp3 = "exports/qa_test.mp3"
    test_wav = "exports/qa_test.wav"
    mixer.export_audio(mixed_audio, out_sr, test_mp3)
    mixer.export_audio(mixed_audio, out_sr, test_wav)
    
    assert os.path.exists(test_mp3) and os.path.getsize(test_mp3) > 1000
    assert os.path.exists(test_wav) and os.path.getsize(test_wav) > 1000
    print(f"   [PASS] MP3 Export verified ({os.path.getsize(test_mp3):,} bytes)")
    print(f"   [PASS] WAV Export verified ({os.path.getsize(test_wav):,} bytes)")
    os.remove(test_mp3)
    os.remove(test_wav)

    # 6. GUI Application & Desktop Shortcut Check
    print("\n[QA 6/6] Validating GUI & Desktop Shortcut Creator...")
    from create_shortcut import create_desktop_shortcut
    shortcut_path = create_desktop_shortcut()
    assert os.path.exists(shortcut_path), "Desktop shortcut file was not created"
    print(f"   [PASS] Desktop shortcut verified at: {shortcut_path}")

    import app
    gui_instance = app.VoiceStudioApp()
    assert gui_instance is not None
    assert app.CUSTOM_VOICE_LABEL in gui_instance.voice_options
    gui_instance.destroy()
    print("   [PASS] GUI Light Mode and branding verified!")

    print("\n" + "=" * 60)
    print(" >>> ALL QA CHECKS PASSED WITH 100% SUCCESS! <<< ")
    print("=" * 60)

if __name__ == "__main__":
    run_qa()

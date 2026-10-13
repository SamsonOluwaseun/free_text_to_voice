"""
Headless CLI for Samlytics VoiceStudio.
Enables AI tools (Claude, ChatGPT, Gemini, Cursor) and terminal pipelines
to synthesize speech, add background music with ducking, and generate .SRT subtitles
without launching any GUI.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from tts_engine import TTSEngine, VOICE_PRESETS
from audio_mixer import AudioMixer
from subtitle_engine import SubtitleEngine
import soundfile as sf
import numpy as np

def resolve_voice_name(query: str) -> str:
    query_lower = query.lower()
    for name in VOICE_PRESETS:
        if query_lower in name.lower():
            return name
    if "abeo" in query_lower or "nigerian" in query_lower:
        return "Nigerian Professional Male"
    return "Nigerian Professional Male"

def cmd_speak(args):
    # 1. Get text content
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[Error] Script file not found: {args.file}")
            sys.exit(1)
        text = file_path.read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        print("[Error] Please provide text via --text or --file")
        sys.exit(1)

    voice_name = resolve_voice_name(args.voice)
    print(f"[*] Voice: {voice_name}")
    print(f"[*] Mode: {'100% Offline' if args.offline else 'Cloud Neural (with Offline Fallback)'}")
    print(f"[*] Speed: {args.speed}x | Pitch Texture: {args.texture}Hz")

    # 2. Synthesize speech
    tts = TTSEngine()
    try:
        speech_audio, sr = tts.synthesize(
            text=text,
            voice_name=voice_name,
            speed_mult=args.speed,
            texture_val=args.texture,
            force_offline=args.offline
        )
    except Exception as e:
        print(f"[Error] Synthesis failed: {e}")
        sys.exit(1)

    print(f"[+] Speech synthesized ({len(speech_audio)/sr:.2f}s)")

    # 3. Optional Background Music Mixing
    mixer = AudioMixer()
    final_audio = speech_audio
    final_sr = sr

    if args.music:
        tracks = mixer.get_available_tracks()
        matched_track = None
        for tname, tpath in tracks.items():
            if args.music.lower() in tname.lower():
                matched_track = (tname, tpath)
                break

        if matched_track:
            print(f"[*] Mixing background track: {matched_track[0]} (Vol: {args.music_vol*100:.0f}%)")
            final_audio, final_sr = mixer.mix(
                speech_data=speech_audio,
                speech_sr=sr,
                music_name=matched_track[0],
                music_volume=args.music_vol,
                speech_volume=args.speech_vol,
                ducking=args.ducking
            )
        else:
            print(f"[Warning] Background music '{args.music}' not found, skipping mix.")

    # 4. Save Audio File
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.suffix.lower() == ".mp3":
        sf.write(str(out_path), final_audio, final_sr, format="MP3")
    else:
        sf.write(str(out_path), final_audio, final_sr)

    print(f"[SUCCESS] Audio saved to: {out_path}")

    # 5. Optional .SRT Subtitle Generation
    if args.srt:
        srt_path = out_path.with_suffix(".srt")
        total_duration = len(final_audio) / final_sr
        try:
            if hasattr(SubtitleEngine, "generate_srt"):
                SubtitleEngine.generate_srt(
                    text=text,
                    total_duration_sec=total_duration,
                    output_filepath=str(srt_path),
                    sentence_boundaries=tts.last_boundaries
                )
            elif hasattr(SubtitleEngine, "generate_srt_from_boundaries") and tts.last_boundaries:
                srt_content = SubtitleEngine.generate_srt_from_boundaries(tts.last_boundaries, total_duration)
                SubtitleEngine.save_srt_file(srt_content, str(srt_path))
            elif hasattr(SubtitleEngine, "generate_srt_from_text_and_duration"):
                srt_content = SubtitleEngine.generate_srt_from_text_and_duration(text, total_duration)
                SubtitleEngine.save_srt_file(srt_content, str(srt_path))
            print(f"[SUCCESS] Subtitles saved to: {srt_path}")
        except Exception as e:
            print(f"[Warning] Subtitle generation notice ({e}), audio was preserved successfully.")

def cmd_list_voices(args):
    tts = TTSEngine()
    has_offline_abeo = tts.offline_engine.has_offline_abeo() if tts.offline_engine else False
    
    print("=" * 65)
    print("  SAMLYTICS VOICESTUDIO — AVAILABLE VOICES")
    print("=" * 65)
    for name, info in VOICE_PRESETS.items():
        is_abeo = "Abeo" in info["id"]
        offline_tag = " (Offline ONNX Ready)" if (is_abeo and has_offline_abeo) else ""
        print(f"\n• {name}{offline_tag}")
        print(f"  ID: {info['id']}")
        print(f"  Description: {info['description']}")
    print("\n" + "=" * 65)

def cmd_list_music(args):
    mixer = AudioMixer()
    tracks = mixer.get_available_tracks()
    print("=" * 65)
    print("  AVAILABLE BACKGROUND STORYTELLING TRACKS")
    print("=" * 65)
    for i, tname in enumerate(tracks.keys(), 1):
        print(f"  {i}. {tname}")
    print("=" * 65)

def main():
    parser = argparse.ArgumentParser(
        description="Samlytics VoiceStudio CLI — Free Local Voice Synthesis & Storytelling for AI and Users"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: speak
    p_speak = subparsers.add_parser("speak", help="Synthesize text into speech audio")
    p_speak.add_argument("text", nargs="?", default="", help="Text to synthesize")
    p_speak.add_argument("--file", "-f", help="Path to .txt or .md script file")
    p_speak.add_argument("--voice", "-v", default="Nigerian Professional Male", help="Voice preset name (default: Abeo)")
    p_speak.add_argument("--speed", "-s", type=float, default=1.0, help="Speed multiplier (0.5 to 2.0, default 1.0)")
    p_speak.add_argument("--texture", "-t", type=int, default=0, help="Pitch texture offset in Hz (-20 to +20)")
    p_speak.add_argument("--out", "-o", default="narration.mp3", help="Output file path (.mp3 or .wav)")
    p_speak.add_argument("--music", "-m", help="Background track name (e.g. 'Lo-Fi', 'Piano', 'Strings')")
    p_speak.add_argument("--music-vol", type=float, default=0.25, help="Music volume (0.0 to 1.0, default 0.25)")
    p_speak.add_argument("--speech-vol", type=float, default=1.0, help="Speech volume (0.0 to 1.5, default 1.0)")
    p_speak.add_argument("--ducking", action="store_true", default=True, help="Enable automatic audio ducking")
    p_speak.add_argument("--no-ducking", dest="ducking", action="store_false", help="Disable audio ducking")
    p_speak.add_argument("--srt", action="store_true", help="Generate synchronized .srt subtitle file")
    p_speak.add_argument("--offline", action="store_true", help="Force 100%% offline neural synthesis")
    p_speak.set_defaults(func=cmd_speak)

    # Subcommand: list-voices
    p_voices = subparsers.add_parser("list-voices", help="List all available voice presets")
    p_voices.set_defaults(func=cmd_list_voices)

    # Subcommand: list-music
    p_music = subparsers.add_parser("list-music", help="List all available background storytelling tracks")
    p_music.set_defaults(func=cmd_list_music)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

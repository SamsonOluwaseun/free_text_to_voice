"""
Model Context Protocol (MCP) Server for Samlytics VoiceStudio.
Enables Claude Desktop, Claude Code, Cursor, and any MCP client to
synthesize speech, create narrations, and export .SRT subtitles directly.

Runs as a standard JSON-RPC 2.0 stdio server with ZERO external MCP dependencies.
"""

import sys
import json
import os
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from tts_engine import TTSEngine, VOICE_PRESETS
from audio_mixer import AudioMixer
from subtitle_engine import SubtitleEngine
import soundfile as sf
import numpy as np

# MCP Tool Schemas
TOOLS = [
    {
        "name": "list_voices",
        "description": "Lists all available voice presets in Samlytics VoiceStudio (including Nigerian Abeo and offline models).",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "list_music_tracks",
        "description": "Lists all available royalty-free background storytelling instrumentals.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "speak_text",
        "description": "Synthesizes text into high-quality speech audio (MP3/WAV) with optional SRT subtitles.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The script or dialogue to synthesize."
                },
                "voice": {
                    "type": "string",
                    "description": "Voice preset name. Defaults to 'Nigerian Professional Male'. Options: 'Nigerian Professional Male', 'Deep Male', 'Soft Male', 'Professional Female 1', 'Professional Female 2'.",
                    "default": "Nigerian Professional Male"
                },
                "speed": {
                    "type": "number",
                    "description": "Speaking speed rate (0.5 to 2.0). 1.0 is normal speed.",
                    "default": 1.0
                },
                "texture": {
                    "type": "integer",
                    "description": "Voice pitch texture adjustment in Hz (-20 to +20). Negative = deeper tone, Positive = crisper tone.",
                    "default": 0
                },
                "output_path": {
                    "type": "string",
                    "description": "Output audio file path (.mp3 or .wav). Defaults to 'exports/speech.mp3'.",
                    "default": "exports/speech.mp3"
                },
                "generate_srt": {
                    "type": "boolean",
                    "description": "If true, generates a synchronized .srt subtitle file alongside the audio.",
                    "default": True
                },
                "offline": {
                    "type": "boolean",
                    "description": "If true, forces 100% offline neural synthesis.",
                    "default": False
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "create_story_narration",
        "description": "Synthesizes text into speech, mixes a background instrumental with automatic audio ducking, and exports synchronized .srt subtitles.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The narration or story text."
                },
                "voice": {
                    "type": "string",
                    "description": "Voice preset name.",
                    "default": "Nigerian Professional Male"
                },
                "music_track": {
                    "type": "string",
                    "description": "Name or keyword of the background music (e.g. 'Lo-Fi', 'Piano', 'Strings', 'Warm Sunrise', 'Acoustic', 'Zen Bells').",
                    "default": "Lo-Fi Night Thoughts"
                },
                "speed": {
                    "type": "number",
                    "description": "Speaking speed rate (0.5 to 2.0). 1.0 is normal speed.",
                    "default": 1.0
                },
                "texture": {
                    "type": "integer",
                    "description": "Voice pitch texture in Hz (-20 to +20). Negative = deeper, Positive = crisper.",
                    "default": 0
                },
                "music_volume": {
                    "type": "number",
                    "description": "Background music volume multiplier (0.0 to 1.0). Default: 0.25",
                    "default": 0.25
                },
                "ducking": {
                    "type": "boolean",
                    "description": "If true, automatically softens music when voice is active.",
                    "default": True
                },
                "offline": {
                    "type": "boolean",
                    "description": "If true, forces 100% offline neural synthesis.",
                    "default": False
                },
                "output_path": {
                    "type": "string",
                    "description": "Output file path (.mp3 or .wav). Defaults to 'exports/story.mp3'.",
                    "default": "exports/story.mp3"
                }
            },
            "required": ["text"]
        }
    }
]

def handle_list_voices():
    tts = TTSEngine()
    has_offline = tts.offline_engine.has_offline_abeo() if tts.offline_engine else False
    voices_info = []
    for name, info in VOICE_PRESETS.items():
        voices_info.append({
            "name": name,
            "id": info["id"],
            "description": info["description"],
            "offline_ready": has_offline if "Abeo" in info["id"] else False
        })
    return {"voices": voices_info}

def handle_list_music():
    mixer = AudioMixer()
    tracks = list(mixer.get_available_tracks().keys())
    return {"music_tracks": tracks}

def handle_speak_text(args):
    text = args.get("text", "").strip()
    voice = args.get("voice", "Nigerian Professional Male")
    speed = float(args.get("speed", 1.0))
    texture = int(args.get("texture", 0))
    out_path_str = args.get("output_path", "exports/speech.mp3")
    generate_srt = bool(args.get("generate_srt", True))
    offline = bool(args.get("offline", False))

    tts = TTSEngine()
    speech_data, sr = tts.synthesize(
        text=text,
        voice_name=voice,
        speed_mult=speed,
        texture_val=texture,
        force_offline=offline
    )

    out_path = Path(out_path_str).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.suffix.lower() == ".mp3":
        sf.write(str(out_path), speech_data, sr, format="MP3")
    else:
        sf.write(str(out_path), speech_data, sr)

    duration_sec = round(len(speech_data) / sr, 2)
    result = {
        "status": "success",
        "audio_file": str(out_path),
        "duration_sec": duration_sec,
        "sample_rate": sr,
        "voice_used": voice
    }

    if generate_srt:
        srt_path = out_path.with_suffix(".srt")
        SubtitleEngine.generate_srt(
            text=text,
            total_duration_sec=duration_sec,
            output_filepath=str(srt_path),
            sentence_boundaries=tts.last_boundaries
        )
        result["subtitle_file"] = str(srt_path)

    return result

def handle_create_story_narration(args):
    text = args.get("text", "").strip()
    voice = args.get("voice", "Nigerian Professional Male")
    music_track = args.get("music_track", "Lo-Fi Night Thoughts")
    music_vol = float(args.get("music_volume", 0.25))
    speed = float(args.get("speed", 1.0))
    texture = int(args.get("texture", 0))
    offline = bool(args.get("offline", False))
    ducking = bool(args.get("ducking", True))
    out_path_str = args.get("output_path", "exports/story.mp3")

    tts = TTSEngine()
    speech_data, sr = tts.synthesize(
        text=text,
        voice_name=voice,
        speed_mult=speed,
        texture_val=texture,
        force_offline=offline
    )

    mixer = AudioMixer()
    tracks = mixer.get_available_tracks()
    matched_track_name = None
    for tname in tracks:
        if music_track.lower() in tname.lower():
            matched_track_name = tname
            break
    if not matched_track_name and tracks:
        matched_track_name = list(tracks.keys())[0]

    final_audio, final_sr = mixer.mix(
        speech_data=speech_data,
        speech_sr=sr,
        music_name=matched_track_name,
        music_volume=music_vol,
        speech_volume=1.0,
        ducking=ducking
    )

    out_path = Path(out_path_str).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.suffix.lower() == ".mp3":
        sf.write(str(out_path), final_audio, final_sr, format="MP3")
    else:
        sf.write(str(out_path), final_audio, final_sr)

    duration_sec = round(len(final_audio) / final_sr, 2)
    srt_path = out_path.with_suffix(".srt")
    SubtitleEngine.generate_srt(
        text=text,
        total_duration_sec=duration_sec,
        output_filepath=str(srt_path),
        sentence_boundaries=tts.last_boundaries
    )

    return {
        "status": "success",
        "audio_file": str(out_path),
        "subtitle_file": str(srt_path),
        "duration_sec": duration_sec,
        "voice_used": voice,
        "music_used": matched_track_name
    }

def process_message(msg):
    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "samlytics-voicestudio",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return None

    elif method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": TOOLS
            }
        }

    elif method == "tools/call":
        params = msg.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        try:
            if tool_name == "list_voices":
                res = handle_list_voices()
            elif tool_name == "list_music_tracks":
                res = handle_list_music()
            elif tool_name == "speak_text":
                res = handle_speak_text(args)
            elif tool_name == "create_story_narration":
                res = handle_create_story_narration(args)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(res, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error executing {tool_name}: {str(e)}"
                        }
                    ]
                }
            }

    else:
        if msg_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not supported: {method}"
                }
            }
        return None

def main():
    # Process JSON-RPC over stdin/stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            resp = process_message(msg)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()


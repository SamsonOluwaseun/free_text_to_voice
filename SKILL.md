---
name: voicestudio
description: Free local text-to-speech, storytelling audio mixer, and .SRT subtitle generator with Nigerian Abeo voice and offline Piper ONNX support.
---

# 🎙️ VoiceStudio AI Skill Guide

Use this skill to generate high-quality voiceovers, tutorial narrations, storytelling audio tracks with ducking, and synchronized `.SRT` video subtitles for free with zero subscriptions.

---

## ⚡ 1. Headless CLI Usage (For AI Agents & Scripts)

AI agents can synthesize voice directly in the terminal without opening any GUI window:

### Basic Speech Synthesis
```bash
python cli.py speak "Welcome to today's tutorial on cloud computing." --voice "Abeo" --out "exports/tutorial.mp3" --srt
```

### Storytelling with Background Instrumental & Audio Ducking
```bash
python cli.py speak "In the heart of Lagos, innovators are building the future." \
  --voice "Abeo" \
  --music "Lo-Fi" \
  --music-vol 0.25 \
  --ducking \
  --out "exports/story.mp3" \
  --srt
```

### Read Script from File (.txt / .md)
```bash
python cli.py speak --file "my_script.md" --voice "Deep Male" --out "exports/narration.wav" --srt
```

### Force 100% Offline Mode (For Network-Blocked Sandboxes)
```bash
python cli.py speak "Running completely offline on CPU." --voice "Abeo" --offline --out "exports/offline.wav"
```

---

## 🤖 2. Model Context Protocol (MCP) Integration for Claude Desktop

To give Claude Desktop direct access to VoiceStudio tools:

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "voicestudio": {
      "command": "python",
      "args": ["<FULL_PATH_TO_REPO>/mcp_server.py"]
    }
  }
}
```

### Available MCP Tools Exposed to Claude:
1. `list_voices`: Discover available voice presets and offline readiness.
2. `list_music_tracks`: Browse the 10 built-in ambient instrumentals.
3. `speak_text`: Synthesize any script to audio (`.mp3`/`.wav`) + `.srt` subtitles.
4. `create_story_narration`: Generate speech + ambient music layer + audio ducking in one step.

---

## 🇳🇬 3. Custom & Open-Source Offline Nigerian Voice Models

VoiceStudio supports offline neural voice models via **Piper ONNX**:

- **Online Mode**: Connects directly to the official neural voice endpoint (`en-NG-AbeoNeural`) for crisp tutorial narrations and video creation.
- **Offline & Legally Compliant Model Training**:
  To train or fine-tune an offline Nigerian voice model safely without breaching cloud terms of service:
  1. **Dataset Sources**: Use **OpenSLR 70** (Google's open-source crowdsourced Nigerian English speech dataset - male subset, CC BY-SA 4.0) or your own voice recordings from `custom_voices/`.
  2. **Fine-Tuning**: Run the Google Colab notebook `train_offline_abeo.ipynb` on a free T4 GPU to fine-tune the male base checkpoint (`en_US-ryan-medium`) on the Nigerian audio dataset.
  3. **Deployment**: Place your trained `en_NG-abeo.onnx` and its `.json` into `offline_models/`. VoiceStudio will automatically detect and synthesize speech 100% offline!

---

## 🎙️ 4. Custom Voice Cloning & Neural Training

VoiceStudio includes zero-shot neural voice cloning and calibration:
- **Audio Formats Supported**: `.m4a`, `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`
- **In-App Mic Recording**: Record 5–30 seconds of speech directly in the desktop app.
- **Voice Training & Calibration**: Dedicated 1-click calibration extracts the cleanest 6–12s acoustic reference, auto-transcribes it via Whisper, and caches the F5-TTS Flow-Matching Diffusion Transformer weights.
- **Privacy & Execution**: Zero cloud API dependencies; neural inference executes 100% locally on your machine.

---

## 🎛️ Voice Options Reference

| Name | ID | Description |
| :--- | :--- | :--- |
| **Nigerian Professional Male** | `en-NG-AbeoNeural` | Articulate Nigerian accent; ideal for tech explainers & tutorials |
| **Deep Male** | `en-US-ChristopherNeural` | Resonant bass-baritone tone; ideal for documentaries & epic stories |
| **Soft Male** | `en-US-AndrewNeural` | Gentle, warm storytelling acoustic tone |
| **Professional Female 1** | `en-US-AvaNeural` | Smooth, warm conversational voice for podcasts & audiobooks |
| **Professional Female 2** | `en-US-AriaNeural` | Crisp executive tone for presentations & news |
| **Custom Cloned Voice** | `🎯 My Cloned Voice` | Personal neural voice clone (Tier 1 Acoustic or Tier 2 F5-TTS Neural) |


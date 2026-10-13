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

## 🇳🇬 3. Nigerian Voice Distillation & Training (`en_NG-abeo.onnx`)

To train the 100% offline Piper ONNX model of the Nigerian Abeo voice:

1. Open `train_offline_abeo.ipynb` in [Google Colab](https://colab.research.google.com/).
2. Select **T4 GPU** runtime.
3. Run all cells:
   - Cell 2 automatically generates 65+ phonetically balanced speech clips using `en-NG-AbeoNeural` in ~2 minutes.
   - Cell 5 fine-tunes the base Piper checkpoint into `en_NG-abeo.onnx`.
4. Download `en_NG-abeo.onnx` and `en_NG-abeo.onnx.json` and place them in `offline_models/`.
5. VoiceStudio automatically recognizes the model and enables offline Nigerian speech!

---

## 🎛️ Voice Options Reference

| Name | ID | Description |
| :--- | :--- | :--- |
| **Nigerian Professional Male** | `en-NG-AbeoNeural` | Articulate Nigerian accent; ideal for tech explainers & tutorials |
| **Deep Male** | `en-US-ChristopherNeural` | Resonant bass-baritone tone; ideal for documentaries & epic stories |
| **Soft Male** | `en-US-AndrewNeural` | Gentle, warm storytelling acoustic tone |
| **Professional Female 1** | `en-US-AvaNeural` | Smooth, warm conversational voice for podcasts & audiobooks |
| **Professional Female 2** | `en-US-AriaNeural` | Crisp executive tone for presentations & news |

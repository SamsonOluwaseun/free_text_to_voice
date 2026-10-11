# 🎙️ VoiceStudio Pro — Local Text-to-Voice & Storytelling Studio

A **100% free, local desktop Text-to-Voice application** for Windows. Convert scripts and stories into natural voice audio, fine-tune voice texture and speed, layer background storytelling music with smart ducking, and export high-fidelity **MP3** or **WAV** files with zero subscription fees.

---

## ✨ Features

- **Curated Professional Voice Presets (Instant Mode - <1s)**:
  - **Nigerian Professional Male**: Clear, engaging, articulate Nigerian accent (*ideal for tutorials, tech explainers, and teaching complex concepts to non-technical audiences*).
  - **Deep Male**: Resonant, authoritative bass-baritone tone (*ideal for documentaries & epic narration*).
  - **Soft Male**: Gentle, calm, conversational acoustic tone (*ideal for bedtime stories & calm narration*).
  - **Professional Female 1**: Smooth, warm, natural conversational voice (*ideal for audiobooks & podcasts*).
  - **Professional Female 2**: Crisp, bright, articulate executive tone (*ideal for business presentations & news*).
- **🎙️ Custom Voice Cloning (Upload Your Voice Recording)**:
  - **100% Free & Local**: Upload a 5–30 second MP3 or WAV recording of your own voice.
  - The app analyzes your vocal register, median pitch fundamental, and spectral resonance profile.
  - Automatically activates **"🎙️ My Uploaded Voice (Custom Clone)"** in the dropdown.
  - Converts any written text into speech matching your vocal timbre and tone.
  - Transparent processing: runs on your laptop's CPU (~15–30s generation time) with a preview button.
- **Voice Texture & Speed Sliders**:
  - **Texture (Pitch / Timbre)**: Slider from deep/resonant to crisp/bright ($-20\text{Hz}$ to $+20\text{Hz}$).
  - **Speed (Rate)**: Slider from $0.50\text{x}$ (slower) to $2.00\text{x}$ (faster).
- **Storytelling Background Instrumentals**:
  - Includes **10 pre-loaded ambient tracks**:
    1. *Ethereal Piano*
    2. *Lo-Fi Night Thoughts*
    3. *Cinematic Story Strings*
    4. *Cozy Acoustic Warmth*
    5. *Deep Space Ambient*
    6. *Gentle Fairytale Harp*
    7. *Nature & Gentle Rain*
    8. *Meditative Zen Bells*
    9. *Mystery & Suspense*
    10. *Warm Sunrise Hope*
  - **Easy Expansion**: Click **"➕ Import Instrumental"** or drop any `.mp3`, `.wav`, or `.ogg` file into the `background_tracks/` folder to use your own music.
  - **Smart Ducking**: Automatically dips the background music level while speech is active so your story narration always stays clear.
  - **Dual Volume Controls**: Independent volume sliders for voice ($0-150\%$) and music ($0-100\%$).
- **Integrated Audio Player**:
  - Play, Pause, Stop controls.
  - Interactive scrubbing seek bar with formatted timestamps (`00:00 / 00:00`).
- **Flexible File Export**:
  - **Download MP3** button.
  - **Download WAV** button.
  - Save directly to your preferred folder with automatic date-stamped file naming.

---

## 🚀 How to Run

### Option 1: Double-Click Launcher
Double-click `run_app.bat` in this folder to launch the app immediately.

### Option 2: Command Line
Open PowerShell or Command Prompt in this folder and run:
```powershell
python app.py
```

---

## 📁 Project Structure

```
Text to voice App/
├── app.py                  # Main CustomTkinter desktop GUI application
├── tts_engine.py           # Neural voice synthesis with pitch/rate tuning & SAPI fallback
├── audio_mixer.py          # Audio mixer, sample rate alignment, ducking, and MP3/WAV export
├── player.py               # SoundDevice audio player with real-time seeking
├── tracks_generator.py     # Generates the 10 starter storytelling instrumentals
├── background_tracks/      # Folder containing all background instrumentals
├── exports/                # Default folder for downloaded MP3 and WAV files
├── requirements.txt        # Python dependency manifest
└── run_app.bat             # 1-click Windows launcher
```

---

## 🎵 Adding Your Own Free Online Instrumentals
1. Find any royalty-free instrumental audio online (e.g., from Free Music Archive, YouTube Audio Library, Pixabay Music, or Incompetech).
2. Click the green **"➕ Import Instrumental"** button in the app, or open the **"📁 Tracks Folder"** and drop your `.mp3` or `.wav` files directly into `background_tracks/`.
3. The new tracks will automatically appear in your background music dropdown!


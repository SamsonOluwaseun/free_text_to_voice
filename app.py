"""
Samlytics VoiceStudio — Local Text-to-Voice & Storytelling App
Branded for Samlytics Data Services with a clean, high-clarity Light theme.
Supports 5 curated neural voice presets (including Nigerian Professional Male),
local custom voice cloning from MP3/WAV uploads, 10 storytelling background
instrumentals with smart ducking, real-time playback, and MP3/WAV export.
100% Free & Local • Zero Subscription Fees.
"""

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import numpy as np
from PIL import Image

from tts_engine import TTSEngine, VOICE_PRESETS
from audio_mixer import AudioMixer
from player import AudioPlayer
from tracks_generator import ensure_starter_tracks
from voice_cloner import VoiceCloner

CUSTOM_VOICE_LABEL = "🎙️ My Uploaded Voice (Custom Clone)"

# Samlytics Brand Colors (from Brand Guidelines)
SAM_BLUE = "#4392F1"
SAM_BLUE_HOVER = "#2563EB"
SAM_DARK = "#00212B"
SAM_CREAM = "#FEFFF8"
SAM_LIME = "#C2E812"
SAM_LIME_BRIGHT = "#DCFF38"
BG_LIGHT = "#F8FAFC"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E2E8F0"
TEXT_MUTED = "#64748B"

# Configure CustomTkinter Appearance
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

SAMPLE_TECH_TUTORIAL = (
    "Welcome! In this tutorial, let us break down how cloud computing works using a simple everyday example. "
    "Think of electricity in your house. You do not build a generator dam in your backyard just to turn on a bulb. "
    "Instead, you simply plug your cable into the wall, and the power company handles the heavy machines and maintenance. "
    "Cloud computing works the exact same way. Instead of buying expensive servers and keeping them in your room, "
    "you simply rent computer power over the internet. It is cheaper, faster, and reliable."
)

SAMPLE_STORY = (
    "In the heart of the ancient forest, beneath the canopy of towering silver birches, "
    "a quiet stream whispered secrets known only to the stars. The traveler paused, listening "
    "to the gentle rustle of leaves as twilight painted the sky in shades of amber and violet. "
    "Here, time seemed to stand still, offering solace to those who dared to wander."
)

SAMPLE_LECTURE = (
    "Welcome students to today's data analytics lecture. Today we will explore why data storytelling "
    "is just as important as writing complex formulas. Having clean numbers is only half the battle; "
    "transforming those numbers into actionable insights that any business leader can understand "
    "is where the real magic happens. Let us dive into our first case study."
)

class VoiceStudioApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Samlytics VoiceStudio — Free Local Text to Voice App")
        self.geometry("1140x840")
        self.minsize(980, 720)
        self.configure(fg_color=BG_LIGHT)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.tracks_dir = os.path.join(self.base_dir, "background_tracks")
        self.exports_dir = os.path.join(self.base_dir, "exports")
        self.custom_voices_dir = os.path.join(self.base_dir, "custom_voices")
        os.makedirs(self.exports_dir, exist_ok=True)
        os.makedirs(self.custom_voices_dir, exist_ok=True)

        # Set Window Icon
        icon_path = os.path.join(self.assets_dir, "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Ensure starter tracks exist
        ensure_starter_tracks(self.tracks_dir)

        # Initialize engines
        self.tts = TTSEngine()
        self.cloner = VoiceCloner(self.custom_voices_dir)
        self.mixer = AudioMixer(self.tracks_dir)
        self.player = AudioPlayer(on_finish_callback=self._on_player_finish)
        self.sample_player = AudioPlayer()

        # Audio state
        self.current_audio_data = None
        self.current_sr = 24000
        self.is_synthesizing = False
        self.user_is_scrubbing = False

        # Build UI
        self._build_header()
        self._build_main_layout()
        self._build_bottom_bar()

        # Scrubber update timer
        self._update_player_ui()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        header_frame.pack(fill="x", padx=20, pady=(15, 8))

        left_brand = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_brand.pack(side="left", padx=15, pady=10)

        # Brand Logo Icon
        logo_png_path = os.path.join(self.assets_dir, "logo_square.png")
        if os.path.exists(logo_png_path):
            try:
                pil_logo = Image.open(logo_png_path)
                self.brand_img = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(38, 38))
                logo_label = ctk.CTkLabel(left_brand, image=self.brand_img, text="")
                logo_label.pack(side="left", padx=(0, 10))
            except Exception:
                pass

        title_box = ctk.CTkFrame(left_brand, fg_color="transparent")
        title_box.pack(side="left")

        title_label = ctk.CTkLabel(
            title_box,
            text="Samlytics VoiceStudio",
            font=ctk.CTkFont(family="Montserrat", size=20, weight="bold"),
            text_color=SAM_DARK
        )
        title_label.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Free Local Text-to-Voice • Neural Presets • Voice Cloning • Background Music Studio",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED
        )
        subtitle.pack(anchor="w")

        # Right Action Buttons
        right_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_box.pack(side="right", padx=15, pady=10)

        # Brand Badge
        badge = ctk.CTkLabel(
            right_box,
            text="100% FREE & LOCAL",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=SAM_DARK,
            fg_color=SAM_LIME_BRIGHT,
            corner_radius=6,
            padx=10,
            pady=3
        )
        badge.pack(side="left", padx=(0, 10))

        btn_exports = ctk.CTkButton(
            right_box,
            text="📂 Saved Audio Folder",
            font=ctk.CTkFont(size=12),
            width=150,
            height=32,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color=SAM_DARK,
            border_width=1,
            border_color=BORDER_COLOR,
            command=self._open_exports_folder
        )
        btn_exports.pack(side="left")

    def _build_main_layout(self):
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(4, 10))
        content_frame.grid_columnconfigure(0, weight=6)
        content_frame.grid_columnconfigure(1, weight=4)
        content_frame.grid_rowconfigure(0, weight=1)

        # === LEFT PANEL: Script & Story Editor ===
        left_panel = ctk.CTkFrame(content_frame, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tb_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        tb_frame.pack(fill="x", padx=16, pady=(14, 8))

        tb_title = ctk.CTkLabel(
            tb_frame,
            text="Script & Story Workspace",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=SAM_DARK
        )
        tb_title.pack(side="left")

        # Utility Buttons
        self.btn_clear = ctk.CTkButton(
            tb_frame,
            text="🗑️ Clear",
            width=65,
            height=26,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color=SAM_DARK,
            command=self._clear_text
        )
        self.btn_clear.pack(side="right", padx=(5, 0))

        self.btn_paste = ctk.CTkButton(
            tb_frame,
            text="📋 Paste",
            width=65,
            height=26,
            fg_color=SAM_BLUE,
            hover_color=SAM_BLUE_HOVER,
            text_color="#FFFFFF",
            command=self._paste_text
        )
        self.btn_paste.pack(side="right", padx=(5, 0))

        # Sample Templates Row
        tpl_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        tpl_row.pack(fill="x", padx=16, pady=(0, 8))

        tpl_label = ctk.CTkLabel(
            tpl_row,
            text="Quick Templates:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_MUTED
        )
        tpl_label.pack(side="left", padx=(0, 6))

        btn_tech = ctk.CTkButton(
            tpl_row,
            text="💡 Tech Tutorial",
            height=24,
            fg_color="#EFF6FF",
            hover_color="#DBEAFE",
            text_color=SAM_BLUE,
            border_width=1,
            border_color="#BFDBFE",
            command=self._load_sample_tutorial
        )
        btn_tech.pack(side="left", padx=(0, 5))

        btn_story = ctk.CTkButton(
            tpl_row,
            text="✨ Storytelling",
            height=24,
            fg_color="#F0FDF4",
            hover_color="#DCFCE7",
            text_color="#16A34A",
            border_width=1,
            border_color="#BBF7D0",
            command=self._load_sample_story
        )
        btn_story.pack(side="left", padx=(0, 5))

        btn_lecture = ctk.CTkButton(
            tpl_row,
            text="🎓 Data Lecture",
            height=24,
            fg_color="#FAF5FF",
            hover_color="#F3E8FF",
            text_color="#9333EA",
            border_width=1,
            border_color="#E9D5FF",
            command=self._load_sample_lecture
        )
        btn_lecture.pack(side="left")

        # Text Editor Box
        self.text_editor = ctk.CTkTextbox(
            left_panel,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word",
            corner_radius=8,
            border_width=1,
            border_color=BORDER_COLOR,
            fg_color="#FAFAFA",
            text_color=SAM_DARK
        )
        self.text_editor.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self.text_editor.insert("1.0", SAMPLE_TECH_TUTORIAL)
        self.text_editor.bind("<KeyRelease>", self._on_text_change)

        # Stats Bar
        self.stats_label = ctk.CTkLabel(
            left_panel,
            text="Characters: 0 • Words: 0",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED
        )
        self.stats_label.pack(anchor="w", padx=16, pady=(0, 12))
        self._on_text_change()

        # === RIGHT PANEL: Voice & Audio Controls ===
        right_panel = ctk.CTkScrollableFrame(
            content_frame,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_COLOR,
            fg_color=CARD_BG
        )
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # --- Section 1: Voice Persona ---
        v_title = ctk.CTkLabel(
            right_panel,
            text="1. Voice Personality",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=SAM_DARK
        )
        v_title.pack(anchor="w", padx=12, pady=(10, 4))

        default_voice = "Nigerian Professional Male"
        self.voice_options = list(VOICE_PRESETS.keys()) + [CUSTOM_VOICE_LABEL]
        self.voice_var = ctk.StringVar(value=default_voice)
        self.voice_dropdown = ctk.CTkOptionMenu(
            right_panel,
            values=self.voice_options,
            variable=self.voice_var,
            command=self._on_voice_selected,
            height=34,
            fg_color=SAM_BLUE,
            button_color=SAM_BLUE_HOVER,
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=SAM_DARK,
            text_color="#FFFFFF",
            dynamic_resizing=False
        )
        self.voice_dropdown.pack(fill="x", padx=12, pady=4)

        self.voice_desc_label = ctk.CTkLabel(
            right_panel,
            text=VOICE_PRESETS[default_voice]["description"],
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            wraplength=340,
            justify="left"
        )
        self.voice_desc_label.pack(anchor="w", padx=12, pady=(2, 6))

        # Custom Voice Upload Box (shown if Custom Clone is selected)
        self.custom_voice_box = ctk.CTkFrame(right_panel, corner_radius=10, fg_color="#F8FAFC", border_width=1, border_color=BORDER_COLOR)
        
        cv_header = ctk.CTkFrame(self.custom_voice_box, fg_color="transparent")
        cv_header.pack(fill="x", padx=12, pady=(8, 2))

        cv_title = ctk.CTkLabel(
            cv_header,
            text="🎙️ Custom Voice Clone",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=SAM_DARK
        )
        cv_title.pack(side="left")

        self.custom_voice_status_label = ctk.CTkLabel(
            self.custom_voice_box,
            text="Upload an MP3/WAV (3-30s) to clone your voice.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            wraplength=330,
            justify="left"
        )
        self.custom_voice_status_label.pack(anchor="w", padx=12, pady=(0, 6))

        cv_btn_row = ctk.CTkFrame(self.custom_voice_box, fg_color="transparent")
        cv_btn_row.pack(fill="x", padx=12, pady=(0, 6))

        self.btn_upload_voice = ctk.CTkButton(
            cv_btn_row,
            text="📤 Upload Voice Recording",
            height=30,
            fg_color="#059669",
            hover_color="#047857",
            text_color="#FFFFFF",
            command=self._upload_custom_voice
        )
        self.btn_upload_voice.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_preview_sample = ctk.CTkButton(
            cv_btn_row,
            text="🔊 Listen",
            width=65,
            height=30,
            state="disabled",
            fg_color="#E2E8F0",
            hover_color="#CBD5E1",
            text_color=SAM_DARK,
            command=self._preview_custom_voice_sample
        )
        self.btn_preview_sample.pack(side="left")

        cv_notice = ctk.CTkLabel(
            self.custom_voice_box,
            text="ℹ️ 100% Free & Local • Runs on CPU (~15-30s per generation)\n⚡ For instant (<1s) generation, choose a Studio Voice above.",
            font=ctk.CTkFont(size=11),
            text_color="#D97706",
            wraplength=330,
            justify="left"
        )
        cv_notice.pack(anchor="w", padx=12, pady=(0, 8))
        self._update_custom_voice_status()

        # --- Section 2: Texture & Speed Controls ---
        p_title = ctk.CTkLabel(
            right_panel,
            text="2. Voice Texture & Speed",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=SAM_DARK
        )
        p_title.pack(anchor="w", padx=12, pady=(12, 4))

        self.texture_label = ctk.CTkLabel(
            right_panel,
            text="Voice Texture: Natural / Balanced (0 Hz)",
            font=ctk.CTkFont(size=13),
            text_color=SAM_DARK
        )
        self.texture_label.pack(anchor="w", padx=12, pady=(2, 2))

        self.texture_slider = ctk.CTkSlider(
            right_panel,
            from_=-20,
            to=20,
            number_of_steps=40,
            button_color=SAM_BLUE,
            progress_color=SAM_BLUE,
            command=self._on_texture_change
        )
        self.texture_slider.set(0)
        self.texture_slider.pack(fill="x", padx=12, pady=(0, 6))

        self.speed_label = ctk.CTkLabel(
            right_panel,
            text="Speaking Speed: 1.00x (Normal)",
            font=ctk.CTkFont(size=13),
            text_color=SAM_DARK
        )
        self.speed_label.pack(anchor="w", padx=12, pady=(4, 2))

        self.speed_slider = ctk.CTkSlider(
            right_panel,
            from_=0.5,
            to=2.0,
            number_of_steps=30,
            button_color=SAM_BLUE,
            progress_color=SAM_BLUE,
            command=self._on_speed_change
        )
        self.speed_slider.set(1.0)
        self.speed_slider.pack(fill="x", padx=12, pady=(0, 14))

        # --- Section 3: Background Story Music ---
        bg_title = ctk.CTkLabel(
            right_panel,
            text="3. Background Story Music",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=SAM_DARK
        )
        bg_title.pack(anchor="w", padx=12, pady=(6, 4))

        self.tracks_dict = self.mixer.get_available_tracks()
        self.track_names = list(self.tracks_dict.keys())
        default_track = self.track_names[1] if len(self.track_names) > 1 else self.track_names[0]

        self.bg_track_var = ctk.StringVar(value=default_track)
        self.bg_dropdown = ctk.CTkOptionMenu(
            right_panel,
            values=self.track_names,
            variable=self.bg_track_var,
            height=34,
            fg_color="#0284C7",
            button_color="#0369A1",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=SAM_DARK,
            text_color="#FFFFFF",
            dynamic_resizing=False
        )
        self.bg_dropdown.pack(fill="x", padx=12, pady=4)

        bg_btn_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        bg_btn_row.pack(fill="x", padx=12, pady=(2, 8))

        btn_import = ctk.CTkButton(
            bg_btn_row,
            text="➕ Import Music",
            height=28,
            fg_color="#059669",
            hover_color="#047857",
            text_color="#FFFFFF",
            command=self._import_custom_instrumental
        )
        btn_import.pack(side="left", expand=True, fill="x", padx=(0, 4))

        btn_folder = ctk.CTkButton(
            bg_btn_row,
            text="📁 Tracks Folder",
            height=28,
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color=SAM_DARK,
            border_width=1,
            border_color=BORDER_COLOR,
            command=self._open_tracks_folder
        )
        btn_folder.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # Volume Controls & Ducking
        vol_frame = ctk.CTkFrame(right_panel, corner_radius=10, fg_color="#F8FAFC", border_width=1, border_color=BORDER_COLOR)
        vol_frame.pack(fill="x", padx=12, pady=(4, 15))

        self.voice_vol_label = ctk.CTkLabel(
            vol_frame,
            text="Speech Volume: 100%",
            font=ctk.CTkFont(size=12),
            text_color=SAM_DARK
        )
        self.voice_vol_label.pack(anchor="w", padx=12, pady=(8, 2))

        self.voice_vol_slider = ctk.CTkSlider(
            vol_frame,
            from_=0.0,
            to=1.5,
            button_color=SAM_BLUE,
            progress_color=SAM_BLUE,
            command=self._on_voice_vol_change
        )
        self.voice_vol_slider.set(1.0)
        self.voice_vol_slider.pack(fill="x", padx=12, pady=(0, 6))

        self.music_vol_label = ctk.CTkLabel(
            vol_frame,
            text="Music Volume: 22%",
            font=ctk.CTkFont(size=12),
            text_color=SAM_DARK
        )
        self.music_vol_label.pack(anchor="w", padx=12, pady=(4, 2))

        self.music_vol_slider = ctk.CTkSlider(
            vol_frame,
            from_=0.0,
            to=1.0,
            button_color=SAM_BLUE,
            progress_color=SAM_BLUE,
            command=self._on_music_vol_change
        )
        self.music_vol_slider.set(0.22)
        self.music_vol_slider.pack(fill="x", padx=12, pady=(0, 8))

        self.ducking_var = ctk.BooleanVar(value=True)
        self.ducking_switch = ctk.CTkSwitch(
            vol_frame,
            text="Smart Ducking (softens music during speech)",
            variable=self.ducking_var,
            font=ctk.CTkFont(size=12),
            text_color=SAM_DARK,
            progress_color=SAM_BLUE
        )
        self.ducking_switch.pack(anchor="w", padx=12, pady=(0, 10))

    def _build_bottom_bar(self):
        bottom_container = ctk.CTkFrame(self, corner_radius=12, border_width=1, border_color=BORDER_COLOR, fg_color=CARD_BG)
        bottom_container.pack(fill="x", padx=20, pady=(4, 15))

        ctrl_row = ctk.CTkFrame(bottom_container, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=16, pady=(12, 6))

        # Main Synthesis Button
        self.btn_generate = ctk.CTkButton(
            ctrl_row,
            text="🎙️ Convert to Voice",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            width=185,
            fg_color=SAM_BLUE,
            hover_color=SAM_BLUE_HOVER,
            text_color="#FFFFFF",
            command=self._start_synthesis
        )
        self.btn_generate.pack(side="left", padx=(0, 15))

        # Transport Controls
        self.btn_play_pause = ctk.CTkButton(
            ctrl_row,
            text="▶ Play",
            width=90,
            height=40,
            state="disabled",
            fg_color="#059669",
            hover_color="#047857",
            text_color="#FFFFFF",
            command=self._toggle_playback
        )
        self.btn_play_pause.pack(side="left", padx=(0, 8))

        self.btn_stop = ctk.CTkButton(
            ctrl_row,
            text="⏹ Stop",
            width=80,
            height=40,
            state="disabled",
            fg_color="#64748B",
            hover_color="#475569",
            text_color="#FFFFFF",
            command=self._stop_playback
        )
        self.btn_stop.pack(side="left", padx=(0, 15))

        # Export Buttons
        self.btn_export_wav = ctk.CTkButton(
            ctrl_row,
            text="💾 Download WAV",
            width=135,
            height=40,
            state="disabled",
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color=SAM_DARK,
            border_width=1,
            border_color=BORDER_COLOR,
            command=lambda: self._export_audio_file("wav")
        )
        self.btn_export_wav.pack(side="right", padx=(6, 0))

        self.btn_export_mp3 = ctk.CTkButton(
            ctrl_row,
            text="💾 Download MP3",
            width=135,
            height=40,
            state="disabled",
            fg_color="#D97706",
            hover_color="#B45309",
            text_color="#FFFFFF",
            command=lambda: self._export_audio_file("mp3")
        )
        self.btn_export_mp3.pack(side="right")

        # Playback Scrubber & Time
        scrub_row = ctk.CTkFrame(bottom_container, fg_color="transparent")
        scrub_row.pack(fill="x", padx=16, pady=(2, 6))

        self.time_label = ctk.CTkLabel(
            scrub_row,
            text="00:00 / 00:00",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=SAM_DARK,
            width=100
        )
        self.time_label.pack(side="left")

        self.scrubber = ctk.CTkSlider(
            scrub_row,
            from_=0,
            to=100,
            button_color=SAM_BLUE,
            progress_color=SAM_BLUE,
            command=self._on_scrubber_slide
        )
        self.scrubber.set(0)
        self.scrubber.pack(side="left", fill="x", expand=True, padx=10)
        self.scrubber.bind("<ButtonPress-1>", lambda e: self._on_scrubber_press())
        self.scrubber.bind("<ButtonRelease-1>", lambda e: self._on_scrubber_release())

        # Status Bar
        status_row = ctk.CTkFrame(bottom_container, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=(0, 10))

        self.progress_bar = ctk.CTkProgressBar(status_row, height=5, progress_color=SAM_BLUE)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 4))
        self.progress_bar.pack_forget()

        self.status_label = ctk.CTkLabel(
            status_row,
            text="Ready. Paste or type your script above and click 'Convert to Voice'.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            anchor="w"
        )
        self.status_label.pack(fill="x")

    # --- UI Event Handlers ---

    def _on_text_change(self, event=None):
        content = self.text_editor.get("1.0", "end-1c")
        chars = len(content)
        words = len(content.split())
        self.stats_label.configure(text=f"Characters: {chars} • Words: {words}")

    def _clear_text(self):
        self.text_editor.delete("1.0", "end")
        self._on_text_change()

    def _paste_text(self):
        try:
            clipboard_text = self.clipboard_get()
            self.text_editor.insert("insert", clipboard_text)
            self._on_text_change()
        except Exception:
            pass

    def _load_sample_story(self):
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", SAMPLE_STORY)
        self._on_text_change()

    def _load_sample_tutorial(self):
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", SAMPLE_TECH_TUTORIAL)
        self._on_text_change()
        self.voice_var.set("Nigerian Professional Male")
        self._on_voice_selected("Nigerian Professional Male")

    def _load_sample_lecture(self):
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", SAMPLE_LECTURE)
        self._on_text_change()
        self.voice_var.set("Nigerian Professional Male")
        self._on_voice_selected("Nigerian Professional Male")

    def _on_voice_selected(self, choice):
        if choice == CUSTOM_VOICE_LABEL:
            self.voice_desc_label.configure(
                text="Synthesizes speech using your uploaded voice timbre, pitch, and acoustic resonance."
            )
            self.custom_voice_box.pack(fill="x", padx=12, pady=(2, 10))
            self._update_custom_voice_status()
        else:
            self.custom_voice_box.pack_forget()
            preset = VOICE_PRESETS.get(choice, {})
            desc = preset.get("description", "")
            self.voice_desc_label.configure(text=desc)

    def _update_custom_voice_status(self):
        profile = self.cloner.get_profile_info()
        if profile and self.cloner.has_uploaded_voice() and hasattr(self, "custom_voice_status_label"):
            fname = profile.get("original_filename", "Custom Sample")
            pitch = profile.get("median_pitch_hz", "N/A")
            dur = profile.get("duration_sec", "N/A")
            self.custom_voice_status_label.configure(
                text=f"✅ Active Voice: {fname}\nPitch: {pitch} Hz • Duration: {dur}s • Base: {profile.get('base_preset', '')}",
                text_color="#059669"
            )
            self.btn_preview_sample.configure(state="normal")
        elif hasattr(self, "custom_voice_status_label"):
            self.custom_voice_status_label.configure(
                text="No voice uploaded yet. Upload an MP3/WAV (3-30s) to clone your voice.",
                text_color=TEXT_MUTED
            )
            self.btn_preview_sample.configure(state="disabled")

    def _upload_custom_voice(self):
        filetypes = [
            ("Audio Files", "*.mp3 *.wav *.m4a *.flac *.ogg"),
            ("MP3 Audio", "*.mp3"),
            ("WAV Audio", "*.wav"),
            ("All Files", "*.*")
        ]
        chosen = filedialog.askopenfilename(
            title="Select Your Voice Recording (3-30 seconds)",
            filetypes=filetypes
        )
        if chosen:
            try:
                profile = self.cloner.register_uploaded_voice(chosen)
                self._update_custom_voice_status()
                messagebox.showinfo(
                    "Voice Upload Successful",
                    f"Analyzed '{profile['original_filename']}'!\n"
                    f"Detected pitch: {profile['median_pitch_hz']} Hz\n"
                    f"Matched vocal register: {profile['base_preset']}\n\n"
                    "Your custom voice profile is now active and ready for speech conversion!"
                )
            except Exception as e:
                messagebox.showerror("Voice Upload Error", f"Could not analyze audio file:\n{e}")

    def _preview_custom_voice_sample(self):
        profile = self.cloner.get_profile_info()
        if profile and os.path.exists(profile.get("sample_path", "")):
            try:
                import soundfile as sf
                data, sr = sf.read(profile["sample_path"])
                self.sample_player.load(data, sr)
                self.sample_player.play()
            except Exception as e:
                messagebox.showerror("Playback Error", f"Could not play sample audio:\n{e}")

    def _on_texture_change(self, value):
        val = int(round(value))
        if val < -3:
            desc = f"Deep / Resonant ({val:+d} Hz)"
        elif val > 3:
            desc = f"Crisp / Bright ({val:+d} Hz)"
        else:
            desc = f"Natural / Balanced ({val:+d} Hz)"
        self.texture_label.configure(text=f"Voice Texture: {desc}")

    def _on_speed_change(self, value):
        val = round(value, 2)
        if val < 0.95:
            desc = f"{val:.2f}x (Slower)"
        elif val > 1.05:
            desc = f"{val:.2f}x (Faster)"
        else:
            desc = f"{val:.2f}x (Normal)"
        self.speed_label.configure(text=f"Speaking Speed: {desc}")

    def _on_voice_vol_change(self, value):
        pct = int(round(value * 100))
        self.voice_vol_label.configure(text=f"Speech Volume: {pct}%")

    def _on_music_vol_change(self, value):
        pct = int(round(value * 100))
        self.music_vol_label.configure(text=f"Music Volume: {pct}%")

    def _import_custom_instrumental(self):
        filetypes = [
            ("Audio Files", "*.mp3 *.wav *.ogg *.flac"),
            ("MP3 Audio", "*.mp3"),
            ("WAV Audio", "*.wav"),
            ("All Files", "*.*")
        ]
        chosen = filedialog.askopenfilename(title="Select Instrumental Audio File", filetypes=filetypes)
        if chosen:
            try:
                dest = self.mixer.import_track(chosen)
                self._refresh_tracks_dropdown()
                base = os.path.basename(dest)
                clean_name = os.path.splitext(base)[0].replace("_", " ").title()
                for k, v in self.tracks_dict.items():
                    if v == dest:
                        self.bg_track_var.set(k)
                        break
                messagebox.showinfo("Import Success", f"Imported '{base}' into your instrumentals library!")
            except Exception as e:
                messagebox.showerror("Import Error", f"Could not import audio file: {e}")

    def _refresh_tracks_dropdown(self):
        self.tracks_dict = self.mixer.get_available_tracks()
        self.track_names = list(self.tracks_dict.keys())
        self.bg_dropdown.configure(values=self.track_names)

    def _open_tracks_folder(self):
        if os.path.exists(self.tracks_dir):
            os.startfile(self.tracks_dir)

    def _open_exports_folder(self):
        if os.path.exists(self.exports_dir):
            os.startfile(self.exports_dir)

    # --- Synthesis Workflow ---

    def _start_synthesis(self):
        text = self.text_editor.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Empty Text", "Please enter or paste some text to convert to speech.")
            return

        if self.is_synthesizing:
            return

        self.player.stop()
        self.btn_play_pause.configure(text="▶ Play", state="disabled")
        self.btn_stop.configure(state="disabled")
        self.btn_export_mp3.configure(state="disabled")
        self.btn_export_wav.configure(state="disabled")

        self.is_synthesizing = True
        self.btn_generate.configure(state="disabled", text="⏳ Converting...")
        self.progress_bar.pack(fill="x", pady=(0, 4))
        self.progress_bar.start()
        self.status_label.configure(text="Synthesizing audio... please wait.")

        voice_name = self.voice_var.get()
        speed_mult = round(self.speed_slider.get(), 2)
        texture_val = int(round(self.texture_slider.get()))
        bg_track_display = self.bg_track_var.get()
        bg_track_path = self.tracks_dict.get(bg_track_display, "")
        voice_vol = self.voice_vol_slider.get()
        music_vol = self.music_vol_slider.get()
        ducking = self.ducking_var.get()

        threading.Thread(
            target=self._synthesis_worker,
            args=(text, voice_name, speed_mult, texture_val, bg_track_path, voice_vol, music_vol, ducking),
            daemon=True
        ).start()

    def _synthesis_worker(self, text, voice_name, speed, texture, bg_path, v_vol, m_vol, ducking):
        try:
            if voice_name == CUSTOM_VOICE_LABEL:
                if not self.cloner.has_uploaded_voice():
                    raise RuntimeError("Please upload an MP3 or WAV recording of your voice first using the 'Upload Voice Recording' button.")
                self.after(0, lambda: self.status_label.configure(
                    text="Cloning your voice and synthesizing speech on CPU... please wait (~15-30s)."
                ))
                raw_voice, sr = self.cloner.clone_and_synthesize(text, speed, texture)
            else:
                raw_voice, sr = self.tts.synthesize(text, voice_name, speed, texture)

            mixed_audio, out_sr = self.mixer.mix_audio(
                voice_data=raw_voice,
                sr=sr,
                bg_track_path=bg_path,
                voice_volume=v_vol,
                bg_volume=m_vol,
                ducking=ducking
            )

            self.after(0, self._synthesis_completed, mixed_audio, out_sr)
        except Exception as e:
            self.after(0, self._synthesis_failed, str(e))

    def _synthesis_completed(self, audio_data: np.ndarray, sr: int):
        self.current_audio_data = audio_data
        self.current_sr = sr
        self.player.load(audio_data, sr)

        self.is_synthesizing = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.btn_generate.configure(state="normal", text="🎙️ Convert to Voice")

        self.btn_play_pause.configure(state="normal", text="▶ Play")
        self.btn_stop.configure(state="normal")
        self.btn_export_mp3.configure(state="normal")
        self.btn_export_wav.configure(state="normal")

        dur = self.player.get_duration()
        self.status_label.configure(
            text=f"Audio generated successfully! Duration: {self._format_time(dur)}. Click Play or Download below."
        )

        self._toggle_playback()

    def _synthesis_failed(self, error_msg: str):
        self.is_synthesizing = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.btn_generate.configure(state="normal", text="🎙️ Convert to Voice")
        self.status_label.configure(text=f"Generation failed: {error_msg}")
        messagebox.showerror("Voice Generation Error", f"An error occurred while generating audio:\n{error_msg}")

    # --- Player Controls & Sync ---

    def _toggle_playback(self):
        if self.current_audio_data is None:
            return

        if self.player.is_playing:
            self.player.pause()
            self.btn_play_pause.configure(text="▶ Play")
        else:
            self.player.play()
            self.btn_play_pause.configure(text="⏸ Pause")

    def _stop_playback(self):
        self.player.stop()
        self.btn_play_pause.configure(text="▶ Play")
        self.scrubber.set(0)

    def _on_player_finish(self):
        self.after(0, self._handle_player_finish_ui)

    def _handle_player_finish_ui(self):
        self.btn_play_pause.configure(text="▶ Play")
        self.scrubber.set(0)

    def _on_scrubber_press(self):
        self.user_is_scrubbing = True

    def _on_scrubber_slide(self, value):
        dur = self.player.get_duration()
        if dur > 0:
            target_sec = (value / 100.0) * dur
            self.time_label.configure(text=f"{self._format_time(target_sec)} / {self._format_time(dur)}")

    def _on_scrubber_release(self):
        self.user_is_scrubbing = False
        dur = self.player.get_duration()
        if dur > 0:
            pct = self.scrubber.get()
            target_sec = (pct / 100.0) * dur
            self.player.seek(target_sec)

    def _update_player_ui(self):
        if not self.user_is_scrubbing and self.current_audio_data is not None:
            pos = self.player.get_position()
            dur = self.player.get_duration()
            if dur > 0:
                pct = (pos / dur) * 100
                self.scrubber.set(pct)
                self.time_label.configure(text=f"{self._format_time(pos)} / {self._format_time(dur)}")
                if self.player.is_playing:
                    self.btn_play_pause.configure(text="⏸ Pause")
                else:
                    self.btn_play_pause.configure(text="▶ Play")

        self.after(120, self._update_player_ui)

    # --- Export Workflow ---

    def _export_audio_file(self, file_format: str):
        if self.current_audio_data is None:
            messagebox.showwarning("No Audio", "Please convert text to voice first before downloading.")
            return

        fmt_upper = file_format.upper()
        default_filename = f"samlytics_voice_{time.strftime('%Y%m%d_%H%M%S')}.{file_format}"

        filetypes = [
            (f"{fmt_upper} Audio File", f"*.{file_format}"),
            ("All Files", "*.*")
        ]

        save_path = filedialog.asksaveasfilename(
            title=f"Save Audio As {fmt_upper}",
            initialdir=self.exports_dir,
            initialfile=default_filename,
            filetypes=filetypes,
            defaultextension=f".{file_format}"
        )

        if save_path:
            try:
                AudioMixer.export_audio(self.current_audio_data, self.current_sr, save_path)
                self.status_label.configure(text=f"Exported successfully: {os.path.basename(save_path)}")
                
                resp = messagebox.askyesno(
                    "Download Complete",
                    f"Saved file successfully!\n\nLocation: {save_path}\n\nWould you like to open the containing folder?"
                )
                if resp:
                    os.startfile(os.path.dirname(save_path))
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to save audio file:\n{e}")

    @staticmethod
    def _format_time(seconds: float) -> str:
        s = int(round(seconds))
        m = s // 60
        s = s % 60
        return f"{m:02d}:{s:02d}"

if __name__ == "__main__":
    app = VoiceStudioApp()
    app.mainloop()

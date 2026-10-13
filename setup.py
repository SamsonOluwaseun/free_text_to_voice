from setuptools import setup, find_packages

setup(
    name="samlytics-voicestudio",
    version="1.0.0",
    description="Free local text-to-voice, storytelling audio mixer, and .SRT subtitle studio with Nigerian voice and offline Piper ONNX support.",
    author="Samlytics Data Services",
    url="https://github.com/SamsonOluwaseun/free_text_to_voice",
    py_modules=[
        "cli",
        "mcp_server",
        "tts_engine",
        "offline_engine",
        "audio_mixer",
        "subtitle_engine",
        "voice_cloner",
        "recorder",
        "tracks_generator"
    ],
    install_requires=[
        "soundfile>=0.14.0",
        "sounddevice>=0.5.6",
        "edge-tts>=7.2.8",
        "pyttsx3>=2.99",
        "Pillow>=10.0.0",
        "scipy>=1.14.0",
        "numpy>=2.0.0",
        "piper-tts>=1.8.0",
        "pywin32>=306; sys_platform == 'win32'",
        "customtkinter>=6.0.0; sys_platform == 'win32'"
    ],
    entry_points={
        "console_scripts": [
            "voicestudio=cli:main"
        ]
    },
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
)

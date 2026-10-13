"""
Abeo Voice Distillation Dataset Generator
Synthesizes a phonetically balanced speech dataset using the Nigerian Professional
Male voice (en-NG-AbeoNeural) to fine-tune an offline Piper VITS ONNX model.

Format: LJSpeech (dataset/wavs/*.wav, dataset/metadata.csv)
Sample Rate: 22050 Hz Mono PCM
"""

import os
import sys
import asyncio
import csv
import subprocess
from pathlib import Path
import edge_tts

# Phonetically balanced sentences + conversational + technical phrases
CURATED_SENTENCES = [
    # Harvard Sentences & Phonetic Benchmarks
    "The birch canoe slid on the smooth planks.",
    "Glue the sheet to the dark blue background.",
    "It is easy to tell the depth of a well.",
    "These days a chicken leg is a rare dish.",
    "Rice is often served in round bowls.",
    "The juice of lemons makes fine punch.",
    "The box was thrown beside the parked truck.",
    "The hogs were fed chopped corn and garbage.",
    "Four hours of steady work faced us.",
    "A large size in stockings is hard to sell.",
    "The boy was there when the sun rose.",
    "A rod is used to catch pink salmon.",
    "The source of the huge river is the clear spring.",
    "Kick the ball straight into the goal.",
    "Help the woman get back to her feet.",
    "A pot of tea helps to pass the evening.",
    "Smoky fires lack flame and heat.",
    "The salt breeze came across from the sea.",
    "The girl was fond of yellow flowers.",
    "Open your mouth and breathe slowly.",
    "A rod of iron will bend with difficulty.",
    "Write a neat letter when you have time.",
    "The fruit peel was curled in bright orange ribbons.",
    "The clock struck twelve as the rain began to fall.",
    "The small pup gnawed a bone on the rug.",
    "Dime after dime fell into the silver slot.",
    "The bright star shone in the northern sky.",
    "Drop the plan if it causes too much trouble.",
    "A white silk jacket goes with any trousers.",
    "A thick black cloud hung over the mountains.",
    
    # Technical, Data & Tutorial Explanations
    "Welcome to today's tutorial on cloud computing and scalable databases.",
    "An application programming interface connects different software systems together seamlessly.",
    "Think of an API like a waiter taking your order to the kitchen.",
    "Cloud infrastructure allows companies to scale resources up or down on demand.",
    "Machine learning models identify complex patterns across massive datasets.",
    "In python, you can define functions to make your code reusable and modular.",
    "A database index speeds up search queries just like an index in a book.",
    "Data analytics transforms raw numbers into clear, actionable business decisions.",
    "Always validate user inputs to protect your web application against vulnerabilities.",
    "Continuous integration ensures that new code updates are tested automatically.",
    "Neural text-to-speech models convert written phonemes into realistic human audio.",
    "Edge computing processes data closer to the source rather than in centralized servers.",
    "Docker containers package your code with all the libraries needed to run anywhere.",
    "Structured query language allows analysts to extract valuable insights from relational tables.",
    "Automating repetitive workflows saves hundreds of engineering hours every month.",

    # Natural Conversational & Storytelling Speech
    "Let me tell you an interesting story about how technology is changing Africa.",
    "In the vibrant city of Lagos, young innovators are building the future with software.",
    "Good morning and thank you for joining our weekly engineering review.",
    "Every journey begins with a single deliberate step forward.",
    "Hard work and dedication will always yield lasting results over time.",
    "Listen carefully to the melody flowing gently beneath the narration.",
    "We need to test every single feature thoroughly before deploying to production.",
    "Thank you for watching this presentation, and do not forget to subscribe.",
    "The sun rose early over the Atlantic coast, casting a warm golden glow across the water.",
    "Curiosity is the engine that drives great scientific discovery.",
    "When you explain a complex concept simply, everyone in the room understands.",
    "Integrity and consistency are the cornerstones of building trust in any team.",
    "Let us explore how neural speech engines generate realistic acoustic formants.",
    "The meeting will commence promptly at ten o'clock tomorrow morning.",
    "Please make sure your audio levels are balanced before starting the podcast.",
    "We are delighted to introduce the next generation of voice synthesis tools.",
    "Great questions are often more valuable than easy answers.",
    "Stay focused, stay persistent, and keep pushing your boundaries every single day.",
    "From software engineering to artificial intelligence, the opportunities are boundless.",
    "Thank you very much for your time and continued support."
]

VOICE_NAME = "en-NG-AbeoNeural"
DATASET_DIR = Path("dataset_abeo")
WAVS_DIR = DATASET_DIR / "wavs"
METADATA_FILE = DATASET_DIR / "metadata.csv"

async def synthesize_sentence(index: int, text: str, semaphore: asyncio.Semaphore):
    file_id = f"abeo_{index:04d}"
    mp3_path = WAVS_DIR / f"{file_id}.mp3"
    wav_path = WAVS_DIR / f"{file_id}.wav"

    async with semaphore:
        try:
            # 1. Synthesize audio via edge-tts
            comm = edge_tts.Communicate(text, VOICE_NAME)
            await comm.save(str(mp3_path))

            # 2. Convert to 22050Hz Mono 16-bit PCM WAV (Piper standard)
            # Use pydub or soundfile
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(mp3_path))
            audio = audio.set_frame_rate(22050).set_channels(1).set_sample_width(2)
            audio.export(str(wav_path), format="wav")

            # Remove temp mp3
            if mp3_path.exists():
                mp3_path.unlink()

            print(f"[{index}/{len(CURATED_SENTENCES)}] Synthesized: {file_id}.wav")
            return file_id, text
        except Exception as e:
            print(f"[!] Error on {file_id}: {e}")
            return None

async def build_dataset():
    WAVS_DIR.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(5)  # 5 concurrent synthesis tasks

    print("=" * 65)
    print(f"  ABEO VOICE DISTILLATION: Generating {len(CURATED_SENTENCES)} clips")
    print(f"  Voice: {VOICE_NAME} -> Piper VITS Format (22050Hz Mono WAV)")
    print("=" * 65)

    tasks = [
        synthesize_sentence(i + 1, sentence, semaphore)
        for i, sentence in enumerate(CURATED_SENTENCES)
    ]
    results = await asyncio.gather(*tasks)

    # Write metadata.csv in LJSpeech format (id|text|normalized_text)
    valid_entries = [r for r in results if r is not None]
    with open(METADATA_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="|")
        for file_id, text in valid_entries:
            writer.writerow([file_id, text, text])

    print("\n" + "=" * 65)
    print(f"  DATASET GENERATION COMPLETE!")
    print(f"  Total audio clips: {len(valid_entries)}")
    print(f"  Output folder: {DATASET_DIR.resolve()}")
    print(f"  Metadata file: {METADATA_FILE.resolve()}")
    print("=" * 65)

def main():
    asyncio.run(build_dataset())

if __name__ == "__main__":
    main()


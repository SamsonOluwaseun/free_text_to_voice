"""
Subtitle Generator Module.
Generates standard SubRip (.srt) subtitle files with precision timestamps,
allowing users and content creators to import captions directly into
video editors like CapCut, Premiere Pro, DaVinci Resolve, or YouTube Studio.
"""

import os
import re

class SubtitleEngine:
    @staticmethod
    def format_srt_timestamp(seconds: float) -> str:
        """Formats seconds into standard SRT format: HH:MM:SS,mmm"""
        seconds = max(0.0, float(seconds))
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int(round((seconds - int(seconds)) * 1000))
        if ms >= 1000:
            s += 1
            ms -= 1000
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @classmethod
    def generate_srt_from_boundaries(cls, boundaries: list[dict], total_audio_duration: float = 0.0) -> str:
        """
        Builds SRT text from captured SentenceBoundary dictionaries.
        Each entry has: {'text': str, 'start': float, 'end': float}
        """
        srt_lines = []
        for idx, entry in enumerate(boundaries, start=1):
            start_str = cls.format_srt_timestamp(entry["start"])
            end_str = cls.format_srt_timestamp(entry["end"])
            text = entry["text"].strip()
            
            srt_lines.append(f"{idx}")
            srt_lines.append(f"{start_str} --> {end_str}")
            srt_lines.append(f"{text}\n")

        return "\n".join(srt_lines)

    @classmethod
    def generate_srt_from_text_and_duration(cls, text: str, total_duration: float) -> str:
        """
        Fallback generator that splits text into clean spoken clauses/sentences
        and distributes timestamps proportionally according to word count.
        """
        # Split text into sentences or major clauses
        raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        if not sentences:
            return ""

        total_words = sum(max(1, len(s.split())) for s in sentences)
        current_time = 0.1  # small 100ms start offset
        boundaries = []

        available_time = max(0.5, total_duration - 0.4)
        for s in sentences:
            words = max(1, len(s.split()))
            dur = (words / total_words) * available_time
            end_time = min(total_duration, current_time + dur)
            boundaries.append({
                "text": s,
                "start": current_time,
                "end": end_time
            })
            current_time = end_time + 0.05  # tiny gap between phrases

        return cls.generate_srt_from_boundaries(boundaries)

    @classmethod
    def save_srt_file(cls, srt_content: str, output_filepath: str):
        """Saves SRT text content to file."""
        if not output_filepath.endswith(".srt"):
            output_filepath += ".srt"
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(srt_content)
        return output_filepath


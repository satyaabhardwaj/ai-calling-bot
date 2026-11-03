import time

import mlx_whisper
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"


def record() -> np.ndarray:
    """Record from the mic until the user presses Enter."""
    chunks = []

    def on_audio(indata, frames, time_info, status):
        chunks.append(indata.copy())

    input("Press Enter to start speaking...")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=on_audio):
        input("🎙️  Recording... press Enter to stop.")
    return np.concatenate(chunks).flatten()


def transcribe(audio: np.ndarray, language: str | None = None) -> str:
    """Turn audio samples into text. To switch engines later, change only this function."""
    result = mlx_whisper.transcribe(audio, path_or_hf_repo=WHISPER_MODEL, language=language)
    return result["text"].strip()


if __name__ == "__main__":
    audio = record()
    print(f"Recorded {len(audio) / SAMPLE_RATE:.1f} seconds")

    start = time.time()
    text = transcribe(audio)
    print(f"You said: {text}")
    print(f"Transcribed in {time.time() - start:.2f} s")
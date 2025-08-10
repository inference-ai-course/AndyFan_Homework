"""ASR using OpenAI Whisper (PyTorch), decoding audio fully in-memory to avoid Windows temp-file locks.

Requirements:
  - pip install openai-whisper pydub numpy
  - ffmpeg installed and on PATH (pydub uses it under the hood)
  - torch installed per your platform: https://pytorch.org/get-started/locally/

Env:
  ASR_MODEL   : tiny|base|small|medium|large-v3 (default: small)
  ASR_DEVICE  : cpu|cuda (default: cpu)
  ASR_LANG    : force language code like 'en'|'zh' (default: auto-detect)
"""
from __future__ import annotations

import os
import io
from typing import Optional

import numpy as np
from pydub import AudioSegment
import whisper

_MODEL = None
_DEVICE = os.getenv("ASR_DEVICE", "cpu").lower()

def _get_model():
    global _MODEL
    if _MODEL is None:
        model_name = os.getenv("ASR_MODEL", "small")
        _MODEL = whisper.load_model(model_name, device=_DEVICE)
    return _MODEL

def _bytes_to_mono16k_float32(audio_bytes: bytes) -> np.ndarray:
    """Decode bytes with pydub+ffmpeg entirely in memory, resample to 16k mono float32 in [-1, 1]."""
    seg = AudioSegment.from_file(io.BytesIO(audio_bytes))     # ffmpeg reads from memory, not from a path
    if seg.frame_rate != 16000:
        seg = seg.set_frame_rate(16000)
    if seg.channels != 1:
        seg = seg.set_channels(1)
    # pydub gives 16-bit PCM samples; convert to float32 [-1,1]
    samples = np.array(seg.get_array_of_samples(), dtype=np.int16)
    audio = samples.astype(np.float32) / 32768.0
    return audio

def transcribe_audio(audio_bytes: bytes, language: Optional[str] = None) -> str:
    if not audio_bytes:
        return ""

    forced_lang = os.getenv("ASR_LANG")
    if forced_lang:
        language = forced_lang

    model = _get_model()

    # Decode fully in memory -> numpy float32 16k mono
    audio = _bytes_to_mono16k_float32(audio_bytes)

    # CPU 下禁用 FP16；用贪心解码更稳
    result = model.transcribe(
        audio=audio,
        language=language,
        fp16=False if _DEVICE == "cpu" else True,
        temperature=0.0,
        no_speech_threshold=0.6,
        logprob_threshold=-1.0,
        compression_ratio_threshold=2.4,
        # 如需 beam search，再加上：
        # beam_size=5, patience=0.2,
    )
    return (result.get("text") or "").strip()

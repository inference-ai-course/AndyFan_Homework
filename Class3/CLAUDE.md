# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a Python-based voice agent system with two main components:

- **Backend (`backend/`)**: FastAPI server that provides a `/chat` endpoint accepting audio or text input. Implements ASR → LLM → TTS pipeline with session-based memory
- **Client (`client/`)**: Gradio web interface for recording/uploading audio and communicating with the backend

### Component Structure

The backend follows a modular design with clear separation of concerns:

- `main.py`: FastAPI application with `/chat` endpoint that orchestrates the full pipeline
- `asr.py`: OpenAI Whisper integration for automatic speech recognition  
- `llm.py`: HuggingFace Transformers pipeline for text generation with chat template support
- `tts.py`: pyttsx3-based text-to-speech conversion to WAV format
- `memory.py`: Simple in-memory conversation history storage using deques, keyed by session ID

The system maintains 5-turn conversation memory per session using `X-Session-ID` headers.

## Development Commands

### Backend Setup
```bash
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env  # Configure model settings
```

### Client Setup  
```bash
cd client
py -3.12 -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Running Services
```bash
# Backend (from backend/)
uvicorn main:app --reload --port 8000

# Client (from client/)
python app.py
```

## Configuration

Backend configuration via `.env` file (copy from `.env.example`):

- **ASR_MODEL**: Whisper model size (tiny/base/small/medium/large-v3)
- **ASR_DEVICE**: Processing device (cpu/cuda)
- **ASR_LANG**: Force language detection (optional)
- **LLM_MODEL**: HuggingFace model ID (default: TinyLlama/TinyLlama-1.1B-Chat-v1.0)
- **LLM_MAX_NEW**: Maximum new tokens for generation
- **LLM_TEMP**: Temperature for text generation
- **HF_TOKEN**: HuggingFace token for private models (optional)

## External Dependencies

- **PyTorch**: Required for Whisper ASR - install separately per platform from https://pytorch.org/get-started/locally/
- **FFmpeg**: Required by both Whisper and pydub for audio processing - install via system package manager
- **HuggingFace Models**: Downloaded automatically on first use, cached locally

## API Interface

The `/chat` endpoint accepts:
- `file`: Audio upload (multipart/form-data)  
- `text`: Text override to bypass ASR (form field)
- `X-Session-ID`: Header for conversation isolation

Returns WAV audio stream with `X-Assistant-Text` header containing the generated response text.
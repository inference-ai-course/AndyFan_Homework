# Voice Agent Backend (FastAPI)

Python 3.12 backend providing `/chat`. Accepts audio or text, keeps 5-turn memory by `X-Session-ID`.
Implements:
- **ASR**: OpenAI Whisper (PyTorch)
- **LLM**: HuggingFace Transformers text-generation pipeline
- **TTS**: pyttsx3 -> WAV

## Quickstart

```bash
# 1) Create and activate venv (Windows)
py -3.12 -m venv .venv
.venv\Scripts\activate

# (macOS/Linux)
# python3.12 -m venv .venv
# source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt

# 2.5) Install PyTorch per your platform (CPU or CUDA):
# https://pytorch.org/get-started/locally/
# Windows CPU example:
# pip install torch --index-url https://download.pytorch.org/whl/cpu

# 3) Install ffmpeg (required by Whisper):
# Windows (choco): choco install ffmpeg
# macOS (brew):   brew install ffmpeg
# Ubuntu/Debian:  sudo apt-get install ffmpeg

# 4) Configure environment
cp .env.example .env
# edit .env if needed (LLM model, language, etc.)

# 5) Run server
uvicorn main:app --reload --port 8000
```

### Endpoint

`POST /chat` (multipart/form-data)
- **file**: UploadFile (audio). Optional if `text` provided.
- **text**: Optional string. If provided, ASR is skipped.
- **X-Session-ID** header: Optional. Use to isolate memory per client.

**Response:** WAV audio (assistant TTS). Also returns `X-Assistant-Text` header with generated text.

### Swap components
- **Whisper ASR** in `asr.py`
- **Transformers LLM** in `llm.py` (change model via `.env`)
- **TTS** in `tts.py` (pyttsx3). Replace with any TTS you like.

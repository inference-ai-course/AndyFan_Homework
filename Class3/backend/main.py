from __future__ import annotations
import io
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Header, Response
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from asr import transcribe_audio
from llm import generate_response
from tts import tts_to_wav_bytes
from memory import get_history, push_turn

load_dotenv()  # Load .env

app = FastAPI(title="Voice Agent Backend", version="0.2.0" )

@app.post("/chat")
async def chat_endpoint(
    response: Response,
    file: UploadFile = File(None),
    text: Optional[str] = Form(None),
    x_session_id: Optional[str] = Header(default="default")
):
    # 1) ASR (or text override)
    if text and text.strip():
        user_text = text.strip()
    else:
        if file is None:
            user_text = "(no audio, no text)"
        else:
            audio_bytes = await file.read()
            user_text = transcribe_audio(audio_bytes)

    # 2) Memory
    history = get_history(x_session_id, max_turns=5)

    # 3) LLM
    assistant_text = generate_response(user_text, history)

    # Save turn
    push_turn(x_session_id, user_text, assistant_text, max_turns=5)

    # 4) TTS
    wav_bytes = tts_to_wav_bytes(assistant_text)

    response.headers["X-Assistant-Text"] = assistant_text
    return StreamingResponse(io.BytesIO(wav_bytes), media_type="audio/wav")

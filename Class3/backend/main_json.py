from __future__ import annotations
import io
import base64
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Header
from dotenv import load_dotenv

from asr import transcribe_audio
from llm import generate_response
from tts import tts_to_wav_bytes
from memory import get_history, push_turn

load_dotenv()  # Load .env

app = FastAPI(title="Voice Agent Backend", version="0.2.0" )

@app.post("/chat")
async def chat_endpoint(
    file: UploadFile = File(None),
    text: Optional[str] = Form(None),
    x_session_id: Optional[str] = Header(default="default")
):
    print(f"[DEBUG] Request received - Session: {x_session_id}")
    
    # 1) ASR (or text override)
    if text and text.strip():
        user_text = text.strip()
        print(f"[DEBUG] Using text: {user_text}")
    else:
        if file is None:
            user_text = "(no audio, no text)"
        else:
            audio_bytes = await file.read()
            print(f"[DEBUG] Processing audio file: {len(audio_bytes)} bytes")
            user_text = transcribe_audio(audio_bytes)

    # 2) Memory
    history = get_history(x_session_id, max_turns=5)

    # 3) LLM
    assistant_text = generate_response(user_text, history)
    print(f"[DEBUG] Generated response: {assistant_text}")

    # Save turn
    push_turn(x_session_id, user_text, assistant_text, max_turns=5)

    # 4) TTS
    wav_bytes = tts_to_wav_bytes(assistant_text)
    print(f"[DEBUG] Generated audio: {len(wav_bytes)} bytes")

    # 5) Encode audio as base64 for JSON response
    audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')
    audio_data_url = f"data:audio/wav;base64,{audio_base64}"

    # Return JSON with both audio and text
    return {
        "audio_url": audio_data_url,
        "text": assistant_text,
        "status": "success"
    }
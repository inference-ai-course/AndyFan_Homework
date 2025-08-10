from __future__ import annotations
import io
import os
import tempfile
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Header, Response
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from asr import transcribe_audio
from llm import generate_response
from tts import tts_to_wav_bytes
from memory import get_history, push_turn

load_dotenv()  # Load .env

# Create tmp directory if it doesn't exist
TMP_DIR = os.path.join(os.path.dirname(__file__), "tmp")
os.makedirs(TMP_DIR, exist_ok=True)

app = FastAPI(title="Voice Agent Backend", version="0.2.0" )

@app.post("/chat")
async def chat_endpoint(
    response: Response,
    file: UploadFile = File(None),
    text: Optional[str] = Form(None),
    x_session_id: Optional[str] = Header(default="default")
):
    print(f"[DEBUG] Request received - Session: {x_session_id}, File: {file.filename if file else None}, Text: {bool(text)}")
    
    # 1) ASR (or text override)
    if text and text.strip():
        print(f"[DEBUG] Using text override: {text}")
        user_text = text.strip()
    else:
        if file is None:
            print("[DEBUG] No audio file or text provided")
            user_text = "(no audio, no text)"
        else:
            audio_bytes = await file.read()
            print(f"[DEBUG] Processing audio file: {file.filename}, size: {len(audio_bytes)} bytes")
            
            # Save uploaded file to tmp folder
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
            upload_filename = f"upload_{timestamp}_{x_session_id}{file_ext}"
            upload_path = os.path.join(TMP_DIR, upload_filename)
            
            with open(upload_path, "wb") as f:
                f.write(audio_bytes)
            print(f"[DEBUG] Saved uploaded file: {upload_path}")
            
            user_text = transcribe_audio(audio_bytes)
            print(f"[DEBUG] Transcribed text: {user_text}")

    # 2) Memory
    history = get_history(x_session_id, max_turns=5)

    # 3) LLM
    print("[DEBUG] Generating LLM response")
    assistant_text = generate_response(user_text, history)
    print(f"[DEBUG] Generated response: {assistant_text}")

    # Save turn
    push_turn(x_session_id, user_text, assistant_text, max_turns=5)

    # 4) TTS
    print("[DEBUG] Converting to speech")
    wav_bytes = tts_to_wav_bytes(assistant_text)
    print(f"[DEBUG] Generated audio: {len(wav_bytes)} bytes")
    
    # Save generated voice response to tmp folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response_filename = f"response_{timestamp}_{x_session_id}.wav"
    response_path = os.path.join(TMP_DIR, response_filename)
    
    with open(response_path, "wb") as f:
        f.write(wav_bytes)
    print(f"[DEBUG] Saved response audio: {response_path}")

    # Ensure assistant_text is properly encoded for header
    try:
        import urllib.parse
        # URL encode the text to handle special characters
        encoded_text = urllib.parse.quote(assistant_text.replace('\n', ' ').replace('\r', ' '))
        response.headers["X-Assistant-Text"] = encoded_text
        print(f"[DEBUG] Original text: {assistant_text}")
        print(f"[DEBUG] Encoded header: {encoded_text}")
    except Exception as e:
        print(f"[DEBUG] Header encoding error: {e}")
        response.headers["X-Assistant-Text"] = urllib.parse.quote("Response generated successfully")
    
    # Verify audio data integrity
    print(f"[DEBUG] Audio data type: {type(wav_bytes)}, length: {len(wav_bytes)}")
    audio_stream = io.BytesIO(wav_bytes)
    print(f"[DEBUG] Audio stream position: {audio_stream.tell()}")
    audio_stream.seek(0)  # Ensure stream starts at beginning
    
    print("[DEBUG] Request completed successfully")
    return StreamingResponse(audio_stream, media_type="audio/wav")
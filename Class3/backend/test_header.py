from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
import io
import urllib.parse

app = FastAPI()

@app.post("/chat")
async def test_chat(response: Response):
    # Test with simple text
    test_text = "Hello world from backend!"
    print(f"[TEST] Original text: {test_text}")
    
    # URL encode
    encoded = urllib.parse.quote(test_text)
    print(f"[TEST] Encoded text: {encoded}")
    
    # Set header
    response.headers["X-Assistant-Text"] = encoded
    print(f"[TEST] Header set successfully")
    
    # Return fake audio (empty WAV)
    fake_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xAC\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    return StreamingResponse(io.BytesIO(fake_wav), media_type="audio/wav")
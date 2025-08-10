from fastapi import FastAPI, Response
import json

app = FastAPI()

@app.post("/chat")
async def test_chat():
    # Return JSON with both audio URL and text
    response_data = {
        "audio_url": "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACEBAAAABkYXRhAAAAAA==",
        "text": "Hello world from backend!",
        "status": "success"
    }
    return response_data
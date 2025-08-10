import gradio as gr
import requests
import io
import base64
import tempfile

BACKEND_URL = "http://127.0.0.1:8000/chat"

def send_audio(mic_audio, file_audio, text_override, session_id):
    files = {}
    data = {}
    headers = {"X-Session-ID": session_id or "default"}

    if text_override and text_override.strip():
        data["text"] = text_override.strip()
    else:
        audio = mic_audio or file_audio
        if audio is None:
            return None, "Please record or upload audio, or use text override.", ""
        if isinstance(audio, str):
            with open(audio, "rb") as f:
                files["file"] = ("audio.mp3", f.read(), "audio/mpeg")
        else:
            sr, y = audio
            import soundfile as sf
            buf = io.BytesIO()
            sf.write(buf, y, samplerate=sr, format="WAV")
            buf.seek(0)
            files["file"] = ("mic.wav", buf, "audio/wav")

    try:
        resp = requests.post(BACKEND_URL, files=files if files else None, data=data if data else None, headers=headers, timeout=120)
        resp.raise_for_status()
        
        # Parse JSON response
        response_data = resp.json()
        print(f"[CLIENT DEBUG] JSON response: {response_data}")
        
        # Extract text
        assistant_text = response_data.get("text", "No text received")
        print(f"[CLIENT DEBUG] Assistant text: '{assistant_text}'")
        
        # Extract and decode audio
        audio_url = response_data.get("audio_url", "")
        if audio_url.startswith("data:audio/wav;base64,"):
            # Decode base64 audio
            audio_base64 = audio_url.replace("data:audio/wav;base64,", "")
            audio_bytes = base64.b64decode(audio_base64)
            
            # Save to temp file for gradio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_bytes)
                audio_path = tmp_file.name
            
            print(f"[CLIENT DEBUG] Saved audio to: {audio_path}")
            return audio_path, assistant_text, ""
        else:
            return None, assistant_text, "Error: Invalid audio data"
            
    except Exception as e:
        print(f"[CLIENT DEBUG] Request failed: {e}")
        return None, "", f"Error: {e}"

with gr.Blocks(title="Voice Agent Client") as demo:
    gr.Markdown("## 🎤 Voice Agent Client")
    with gr.Row():
        backend_url = gr.Textbox(value=BACKEND_URL, label="Backend URL", interactive=True)
        session_id = gr.Textbox(value="demo-user", label="Session ID", interactive=True)

    def update_url(url):
        global BACKEND_URL
        BACKEND_URL = url
        return f"Backend set to: {url}"

    set_btn = gr.Button("Set Backend URL")
    url_status = gr.Markdown()
    set_btn.click(update_url, inputs=[backend_url], outputs=[url_status])

    gr.Markdown("### Input")
    mic = gr.Audio(sources=["microphone"], type="filepath", label="Record")
    file_u = gr.Audio(sources=["upload"], type="filepath", label="Upload file")
    text_override = gr.Textbox(label="(Optional) Text override (skip ASR)", placeholder="Type here to bypass ASR")

    submit = gr.Button("Send")
    with gr.Row():
        out_audio = gr.Audio(label="Assistant Audio (WAV)", autoplay=True)
        out_text = gr.Textbox(label="Assistant Text")
    err = gr.Markdown()

    submit.click(send_audio, inputs=[mic, file_u, text_override, session_id], outputs=[out_audio, out_text, err])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7861, share=True)
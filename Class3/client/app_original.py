import gradio as gr
import requests
import io

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
        
        # Debug response
        print(f"[CLIENT DEBUG] Response status: {resp.status_code}")
        print(f"[CLIENT DEBUG] Response headers: {dict(resp.headers)}")
        print(f"[CLIENT DEBUG] Response content length: {len(resp.content)}")
        
        # Check all possible header variations
        print("[CLIENT DEBUG] Checking all headers for assistant text:")
        for key, value in resp.headers.items():
            if 'assistant' in key.lower() or 'text' in key.lower():
                print(f"[CLIENT DEBUG] Found header: {key} = '{value}'")
        
        assistant_text_raw = resp.headers.get("X-Assistant-Text", "")
        print(f"[CLIENT DEBUG] X-Assistant-Text header: '{assistant_text_raw}'")
        print(f"[CLIENT DEBUG] X-Assistant-Text header exists: {bool(assistant_text_raw)}")
        print(f"[CLIENT DEBUG] X-Assistant-Text header length: {len(assistant_text_raw)}")
        
        # Also check case variations
        alt_headers = ["x-assistant-text", "X-assistant-text", "x-Assistant-Text"]
        for alt_header in alt_headers:
            alt_value = resp.headers.get(alt_header, "")
            if alt_value:
                print(f"[CLIENT DEBUG] Found alternative header {alt_header}: '{alt_value}'")
                assistant_text_raw = alt_value
        
        # Decode URL-encoded text from header
        import urllib.parse
        try:
            assistant_text = urllib.parse.unquote(assistant_text_raw) if assistant_text_raw else "No text received"
            print(f"[CLIENT DEBUG] Final decoded text: '{assistant_text}'")
            print(f"[CLIENT DEBUG] Final text length: {len(assistant_text)}")
        except Exception as e:
            print(f"[CLIENT DEBUG] Decode error: {e}")
            assistant_text = assistant_text_raw or "Decode failed"
        
        # Verify audio content
        if len(resp.content) == 0:
            return None, "", "Error: Empty audio response"
        
        # Save audio to temp file for gradio (gradio prefers file paths)
        import tempfile
        import os
        if len(resp.content) > 0:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(resp.content)
                tmp_path = tmp_file.name
            print(f"[CLIENT DEBUG] Saved response audio to: {tmp_path}")
            return tmp_path, assistant_text, ""
        else:
            return None, assistant_text, "Error: Empty audio response"
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

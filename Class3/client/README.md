# Voice Agent Client (Gradio)

Simple UI to record or upload audio and send to FastAPI backend.
Also supports a text override (bypasses ASR).

## Quickstart

```bash
# 1) Create & activate venv (Windows)
py -3.12 -m venv .venv
.venv\Scripts\activate

# (macOS/Linux)
python3.12 -m venv .venv
source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt

# 3) Run client
python app.py
# Visit the printed URL; set the backend URL if not default.
```

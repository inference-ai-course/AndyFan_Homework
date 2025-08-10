import io
import pyttsx3
from pydub import AudioSegment

def tts_to_wav_bytes(text: str) -> bytes:
    engine = pyttsx3.init()
    import tempfile, os
    with tempfile.TemporaryDirectory() as td:
        out_path = os.path.join(td, "out.wav")
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        seg = AudioSegment.from_file(out_path)
        buf = io.BytesIO()
        seg.export(buf, format="wav")
        return buf.getvalue()

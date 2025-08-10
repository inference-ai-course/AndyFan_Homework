from __future__ import annotations
import os
from typing import List, Tuple, Optional

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

_SYSTEM_PROMPT = """You are a concise, helpful voice assistant. 
Answer clearly, keep responses brief unless asked for details.
"""

_tokenizer = None
_model = None
_pipe = None

def _init_model():
    global _tokenizer, _model, _pipe
    if _pipe is not None:
        return _pipe
    model_name = os.getenv("LLM_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    use_auth_token = os.getenv("HF_TOKEN") or None
    _tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=use_auth_token)
    _model = AutoModelForCausalLM.from_pretrained(model_name, use_auth_token=use_auth_token)
    _pipe = pipeline(
        "text-generation",
        model=_model,
        tokenizer=_tokenizer,
        device_map="auto" if os.getenv("ASR_DEVICE", "cpu") == "cuda" else None,
    )
    return _pipe

def _history_to_messages(history: List[Tuple[str, str]], user_text: str):
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    for u, a in history[-5:]:
        messages.append({"role": "user", "content": u})
        messages.append({"role": "assistant", "content": a})
    messages.append({"role": "user", "content": user_text})
    return messages

def _apply_chat_template(tokenizer, messages: list[str], add_generation_prompt: bool=True) -> Optional[str]:
    if hasattr(tokenizer, "apply_chat_template") and callable(getattr(tokenizer, "apply_chat_template")):
        try:
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=add_generation_prompt)
        except Exception:
            return None
    return None

def generate_response(user_text: str, history: List[Tuple[str, str]]) -> str:
    if not user_text or not user_text.strip():
        user_text = "(no input detected)"
    pipe = _init_model()

    messages = _history_to_messages(history, user_text)
    prompt = _apply_chat_template(_pipe.tokenizer, messages)
    if prompt is None:
        # Fallback manual prompt
        convo = "\n".join([f"User: {u}\nAssistant: {a}" for u, a in history[-5:]])
        prompt = f"{_SYSTEM_PROMPT}\n{convo}\nUser: {user_text}\nAssistant:"

    max_new = int(os.getenv("LLM_MAX_NEW", "128"))
    temperature = float(os.getenv("LLM_TEMP", "0.7"))

    out = pipe(
        prompt,
        max_new_tokens=max_new,
        do_sample=True,
        temperature=temperature,
        top_p=0.9,
        eos_token_id=_pipe.tokenizer.eos_token_id,
        pad_token_id=_pipe.tokenizer.eos_token_id,
    )[0]["generated_text"]

    # If chat template was used, generated_text includes the prompt. Extract tail after prompt.
    if out.startswith(prompt):
        out = out[len(prompt):]

    # Basic trimming
    return out.strip().split("\n")[0].strip() or "(no output)"

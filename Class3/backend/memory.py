from collections import deque
from typing import Deque, Dict, List, Tuple

# Simple in-memory store: session_id -> deque of (user, assistant)
_CONV: Dict[str, Deque[Tuple[str, str]]] = {}

def get_history(session_id: str, max_turns: int = 5) -> List[Tuple[str, str]]:
    dq = _CONV.get(session_id)
    if not dq:
        return []
    # Return list copy
    return list(dq)[-max_turns:]

def push_turn(session_id: str, user_text: str, assistant_text: str, max_turns: int = 5) -> None:
    if session_id not in _CONV:
        _CONV[session_id] = deque(maxlen=max_turns)
    _CONV[session_id].append((user_text, assistant_text))

from pydantic import BaseModel

class ChatSessionOut(BaseModel):
    session_id: str
    user_id: str
    question: str
    answer: str
    tokens: int
    timestamp: str  # oppure datetime, se preferisci
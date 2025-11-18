from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import ChatSession
from pydantic import BaseModel

router = APIRouter()

class UpdatePromptRequest(BaseModel):
    session_id: str
    new_prompt: str

@router.post("/update_prompt/")
def update_prompt(request: UpdatePromptRequest, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter_by(session_id=request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    session.system_prompt = request.new_prompt
    db.commit()
    return {"status": "ok", "session_id": request.session_id, "system_prompt": request.new_prompt}

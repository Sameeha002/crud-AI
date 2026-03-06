
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Message

router = APIRouter(prefix="/api", tags=["Messages"])

@router.delete("/threads/{thread_id}/messages/truncate")
def truncate_messages_from_index(thread_id: int, from_index: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(
        Message.thread_id == thread_id
    ).order_by(Message.id).all()

    messages_to_delete = messages[from_index:]
    ids_to_delete = [msg.id for msg in messages_to_delete]

    if ids_to_delete:
        db.query(Message).filter(
            Message.id.in_(ids_to_delete)
        ).delete(synchronize_session=False)
        db.commit()

    return {"message": "Messages truncated successfully"}
from fastapi import Depends, APIRouter, HTTPException
from database import SessionLocal
from models import  User, ChatThread, Message, UserCreate, ChatCreate, Feedback, FeedbackRequest, FeedbackResponse
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(
    prefix = "/users",
    tags = ["Users"]
)

@router.get('/')
def get_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.post('/get-or-create')
def get_or_create_user(user: UserCreate, db:Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        return{
            "id": existing.id,
            "name": existing.name,
            "email": existing.email
        }
    
    new_user = User(
        name = user.name,
        email = user.email
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {
        "id" : new_user.id,
        "name" : new_user.name,
        "email": new_user.email
        }
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed creating new user"
        )


@router.post('/create-chat')
def create_new_chat(chat: ChatCreate, db: Session = Depends(get_db)):
    new_chat = ChatThread(
        user_id= chat.user_id,
        title = chat.title
    )
    try: 
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)

        return new_chat
    except HTTPException:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed creating new chat"
        )


@router.get('/{user_id}/chats')
def get_all_chat_for_user(user_id: str, db:Session = Depends(get_db)):
    chats = db.query(ChatThread).filter(ChatThread.user_id == user_id).order_by(ChatThread.created_at.desc()).all()

    return chats

@router.get("/chats/{thread_id}/messages")
def get_chat_messages(thread_id: int, db: Session = Depends(get_db)):
    messages = (
        db.query(Message)
        .filter(Message.thread_id == thread_id)
        .order_by(Message.created_at)
        .all()
    )
    return messages
  
@router.post("/chats/{thread_id}/messages/{message_id}/feedback", response_model= FeedbackResponse)
def get_feedback(thread_id: int, message_id: int,feedback: FeedbackRequest ,db: Session = Depends(get_db)):
    existing = db.query(Feedback).filter(Feedback.message_id == message_id).first()

    if existing:
        existing.feedback_type = feedback.feedback_type
        existing.reason = feedback.reason
        try:
            db.commit()
           
            return {
                "id": existing.id,
                "message_id": existing.message_id,
                "thread_id": existing.thread_id,
                "feedback_type": existing.feedback_type,
                "reason": existing.reason,
            }
        except HTTPException:
            db.rollback()
            raise HTTPException(
            status_code=500,
            detail="Failed updating existing feedback"
        )

    new_feedback = Feedback(
        message_id = message_id,
        thread_id = thread_id,
        feedback_type  = feedback.feedback_type,
        reason = feedback.reason
    )
    try:
        db.add(new_feedback)
        db.commit()
        db.refresh(new_feedback)
        return {
            "id": new_feedback.id,
            "message_id": new_feedback.message_id,
            "thread_id": new_feedback.thread_id,
            "feedback_type": new_feedback.feedback_type,
            "reason": new_feedback.reason,
        }
    except HTTPException:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed creating new feedback"
        )
    

@router.get("/feedback")
def get_all_feedback(db: Session = Depends(get_db)):
    feedback = db.query(Feedback).all()
    return feedback
from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from datetime import datetime
import enum
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import relationship

class FeedbackType(str, enum.Enum):
    like = "like"
    dislike = "dislike"

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    thread_id = Column(Integer, ForeignKey("chat_threads.id"), nullable=False)
    feedback_type = Column(Enum(FeedbackType), nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    message  = relationship("Message", back_populates = "feedback", lazy="noload")
    thread = relationship("ChatThread", back_populates = "feedback", lazy="noload")

# schema
class FeedbackRequest(BaseModel):
    feedback_type: FeedbackType
    reason: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    message_id: int
    thread_id: int
    feedback_type: FeedbackType
    reason: Optional[str] = None

    class Config:
        from_attributes= True
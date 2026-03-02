from sqlalchemy import String, Integer, Column, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from pydantic import BaseModel
from typing import Optional

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("chat_threads.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    tool_calls = Column(JSON, nullable = True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    thread = relationship("ChatThread", back_populates = "messages")
    feedback = relationship("Feedback", back_populates="message", uselist=False, lazy="noload")
   
# schema
class MessageCreate(BaseModel):
    thread_id: Optional[int] = None
    content: str
    user_id: Optional[str] = None

class MessageResponse(BaseModel):
    id: int
    thread_id: int
    role: str
    content: str 
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True




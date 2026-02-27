from sqlalchemy import String, Column
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True, default = lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)

    threads = relationship("ChatThread", back_populates = "user")
   

class UserCreate(BaseModel):
    name: str
    email:str



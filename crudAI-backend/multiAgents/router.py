from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from database import get_db
from models import User
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .graph.multi_agent_graph import graph

router = APIRouter(prefix="/api/v1/agents", tags=["MultiAgents"])

class AgentRequest(BaseModel):
    user_id: str
    thread_id: int
    input: str 

@router.post("/run")
async def run_agent(payload: AgentRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    config = {"configurable": {"thread_id": payload.thread_id}}
    
    result = await graph.ainvoke({
        "messages": [HumanMessage(content=payload.input)],
        "loaded_memory": ""
    }, config=config)

    last_message = result["messages"][-1]

    content = last_message.content
    if isinstance(content, list):
        # extract text from list format [{"type": "text", "text": "..."}]
        content = " ".join(
            item.get("text", "") for item in content if isinstance(item, dict)
        )

    return {
        "response": content or "No response from agent."
    }
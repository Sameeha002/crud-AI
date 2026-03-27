from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from database import get_db, SessionLocal
from models import User, Message, ChatThread
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .graph.multi_agent_graph import graph
from langchain_core.messages import HumanMessage as HumanMsg
import json

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
    
    # create a new thread_id if thread_id is 0
    thread_id = payload.thread_id
    if thread_id == 0:
        with SessionLocal() as db:
            new_thread = ChatThread(user_id = payload.user_id, title= payload.input[:30])
            try:
                db.add(new_thread)
                db.commit()
                db.refresh(new_thread)
                thread_id = new_thread.id
            except:
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="Failed creating new thread id"
                )
         
    # save user msg to db
    with SessionLocal() as db:
        user_msg = Message(thread_id = thread_id, role = "user", content = payload.input)
        try:
            db.add(user_msg)
            db.commit()
            db.refresh(user_msg)
        except:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed saving user message to database"
            )
    
    config = {"configurable": {"thread_id": thread_id}}
    
    result = await graph.ainvoke({
        "messages": [HumanMessage(content=payload.input)],
        "loaded_memory": ""
    }, config=config)

    tool_calls = []
    tool_results = []
    final_response = []

    messages = result["messages"]
    last_human_idx = max(
        (i for i, m in enumerate(messages)if isinstance(m, HumanMsg)),
        default=0
    )
    routed_to = None
    for msg in messages[last_human_idx + 1:]:
        
        if isinstance(msg, tuple):
            continue
        print(f"MSG TYPE: {msg.type}, CONTENT: {repr(msg.content)[:200]}")

        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tool in msg.tool_calls:
                tool_calls.append({
                    "tool": tool["name"],
                    "args": tool["args"]
                })

        elif msg.type == "tool":
            tool_results.append({
                "tool": msg.name,
                "content": msg.content
            })

        elif msg.type == "ai":
            content = msg.content
            if isinstance(content, str) and content.startswith("__routed_to__"):
                routed_to = content.replace("__routed_to__","").strip()
                continue
            if isinstance(content, list):
                content = " ".join(
                    item.get("text", "") for item in content if isinstance(item, dict)
                )
            if content:
                final_response = content

    structured_content = [
        *([ {"type": "routed_to", "agent": routed_to} ] if routed_to else []),
        *[{"type": "tool_call", "tool": tc["tool"]} for tc in tool_calls],
        *[{"type": "tool_result", "tool": tr["tool"], "content": tr["content"]} for tr in tool_results],
        {"type": "text", "content": final_response or "No response from agent."},
    ]

    # save ai message
    message_id = None
    with SessionLocal() as db:
        agent_msg = Message(
            thread_id = thread_id,
            role = "assistant",
            content = json.dumps(structured_content),
            tool_calls = tool_calls if tool_calls else None,
        )
        try:
            db.add(agent_msg)
            db.commit()
            db.refresh(agent_msg)
            message_id = agent_msg.id
        except:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed saving agent message"
            )
                
    return {
        "response": final_response or "No response from agent.",
        "tool_calls": tool_calls,
        "tool_results" : tool_results,
        "message_id": message_id,
        "thread_id": thread_id,
        "routed_to": routed_to,
    }
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from agent import agent
from models import Message, ChatThread
import json

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"]
)

@router.websocket("/chat/{thread_id}")
async def websocket_chat(websocket: WebSocket, thread_id: int, db: Session = Depends(get_db)):
    await websocket.accept()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            user_content = data.get("content")
            user_id = data.get("user_id")

            # Create thread if needed
            if thread_id == 0:
                new_thread = ChatThread(user_id=user_id, title=user_content[:30])
                db.add(new_thread)
                db.commit()
                db.refresh(new_thread)
                thread_id = new_thread.id

            # Save user message
            user_msg = Message(thread_id=thread_id, role="user", content=user_content)
            try:
                db.add(user_msg)
                db.commit()

            except HTTPException:
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="Failed SAVING USER MESSAGE"
                )

            # Stream agent response
            full_response = ""
            tool_log = []
            structured_response = []
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            async for event in agent.astream_events(
                {"messages": [("user", user_content)]},
                config={"configurable": {"thread_id": str(thread_id)}},
                version='v2'
            ):
                kind = event.get("event")

                if kind == "on_tool_start":
                    tool_name = event.get("name", "unknown_tool")
                    tool_data = {"type": "tool_call", "tool": tool_name}
                    tool_log.append(tool_data)
                    structured_response.append(tool_data)
                    await websocket.send_json(tool_data)

                if kind == "on_tool_end":
                    tool_name = event.get("name", "unknown_tool")
                    output = event.get("data", {}).get("output", "")
                    result_output = output.content if hasattr(output, "content") else str(output)
                    tool_result = {"type": "tool_result", "tool": tool_name, "content": result_output}
                    structured_response.append(tool_result)
                    await websocket.send_json(tool_result)

                if kind == "on_chat_model_stream":
                    content = event.get("data", {}).get("chunk", {})
                    if hasattr(content, "content") and content.content:
                        token = content.content
                        full_response += token
                        await websocket.send_json({"type": "text", "content": token})

                if kind == "on_chat_model_end":
                    usage = event.get("data", {}).get("output", {})
                    if hasattr(usage, "usage_metadata") and usage.usage_metadata:
                        prompt_tokens += usage.usage_metadata.get("input_tokens", 0)
                        completion_tokens += usage.usage_metadata.get("output_tokens", 0)
                        total_tokens += usage.usage_metadata.get("total_tokens", 0)

            # Save assistant message
            if full_response:
                structured_response.append({"type": "text", "content": full_response})
                agent_msg = Message(
                    thread_id=thread_id,
                    role="assistant",
                    content=json.dumps(structured_response),
                    tool_calls=tool_log if tool_log else None,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                )
                db.add(agent_msg)
                db.commit()
                db.refresh(agent_msg)

                await websocket.send_json({"type": "message_id", "message_id": agent_msg.id})

    except WebSocketDisconnect:
        print(f"Client disconnected from thread {thread_id}")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
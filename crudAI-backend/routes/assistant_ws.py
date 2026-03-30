from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from database import SessionLocal
from agent import agent
from models import Message, ChatThread
import json, asyncio
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"]
)

@router.websocket("/chat/{thread_id}")
async def websocket_chat(websocket: WebSocket, thread_id: int):
    await websocket.accept()
    stop_request = False

    try:   
        while True: 
            
            data = await websocket.receive_json()
            if data.get("type") == "stop":
                continue

            if data.get("type") == "regenerate":
                message_id = data.get("message_id")
                full_response = ""
                tool_log = []
                structured_response = []
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0

                with SessionLocal() as db:
                    all_messages = db.query(Message).filter(
                        Message.thread_id == thread_id
                    ).order_by(Message.id).all()

                    agent_index = next(
                        (i for i, m in enumerate(all_messages) if m.id == message_id), None
                    )
                    original_user_content = None
                    if agent_index is not None and agent_index > 0:
                        original_user_content = all_messages[agent_index - 1].content

                    if not original_user_content:
                        await websocket.send_json({"type": "error", "message": "Could not find original user message"})
                        continue

                async for event in agent.astream_events(
                    {"messages": [("user", original_user_content)]},
                    config={"configurable": {"thread_id": str(thread_id)}},
                    version='v2'
                ):
                    try:
                        incoming = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)
                        if incoming.get("type") == "stop":
                            stop_request = True
                    except asyncio.TimeoutError:
                        pass
                    except Exception:
                        pass

                    if stop_request:
                        break

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

             
                if full_response:
                    structured_response.append({"type": "text", "content": full_response})
                    with SessionLocal() as db:
                        msg = db.query(Message).filter(Message.id == message_id).first()
                        if msg:
                            msg.content = json.dumps(structured_response)
                            msg.tool_calls = tool_log if tool_log else None
                            msg.prompt_tokens = prompt_tokens
                            msg.completion_tokens = completion_tokens
                            msg.total_tokens = total_tokens
                            db.commit()

                    await websocket.send_json({"type": "message_id", "message_id": message_id})

                continue  

            if data.get("type") == "edit_message":
                from_index = data.get("from_index")
                with SessionLocal() as db:
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
                    
                    data["type"] = "message"
                    
            # Receive message from client
            user_content = data.get("content")
            user_id = data.get("user_id")
            stop_request = False

            # Create thread if needed
            if thread_id == 0:
                with SessionLocal() as db:
                    new_thread = ChatThread(user_id=user_id, title=user_content[:30])
                    db.add(new_thread)
                    db.commit()
                    db.refresh(new_thread)
                    thread_id = new_thread.id
                    
                await websocket.send_json({
                    "type": "thread_id",
                    "thread_id": thread_id
                })

            # Save user message
            with SessionLocal() as db:
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
                try:
                    incoming = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)
                    if incoming.get("type") == "stop":
                        stop_request = True
                except asyncio.TimeoutError:
                    pass
                except Exception:
                    pass

                if stop_request:
                    break

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
                with SessionLocal() as db:
                    db.add(agent_msg)
                    db.commit()
                    db.refresh(agent_msg)
                    await websocket.send_json({"type": "message_id", "message_id": agent_msg.id})

    except WebSocketDisconnect:
        print(f"Client disconnected from thread {thread_id}")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
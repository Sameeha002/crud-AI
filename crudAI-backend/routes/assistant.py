from fastapi import APIRouter, Depends, HTTPException, Request
from agent import agent
from models import Message, MessageCreate, ChatThread
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy.exc import SQLAlchemyError
from sse_starlette.sse import EventSourceResponse 
import traceback
import json

router = APIRouter(
    prefix="/assistant",
    tags=["Assistant-SSE"]
)

@router.post('/')
async def chat_with_agent(req: MessageCreate, request: Request , db: Session = Depends(get_db)):

    # create thread_id
    if req.thread_id is None:
        if req.user_id is None:
            raise HTTPException(
                status_code=422,
                detail="user_id is required when creating a new chat thread"
            )
        new_thread = ChatThread(user_id = req.user_id,title = req.content[:30])
        db.add(new_thread)
        db.commit()
        db.refresh(new_thread)
        thread_id = new_thread.id
    else:
        thread_id = req.thread_id

    # save user message
    user_msg = Message(
        thread_id = thread_id,
        role = "user",
        content = req.content
    )
    try:
        db.add(user_msg)
        db.commit()

    except HTTPException:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed SAVING USER MESSAGE"
        )
    

    # call ai agent
    async def event_generator():
        full_response = ""
        tool_log = []
        structured_response = []
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        try:
            async for event in agent.astream_events(
                {
                    "messages": [("user", req.content)]
                },
                config={
                    "configurable": {
                        "thread_id": str(thread_id)
                    }
                },  
                version='v2'
            ):
                
            # Stop if client disconnects
                if await request.is_disconnected():
                    print("Client disconnected")
                    break

                kind = event.get("event")

                if kind == "on_tool_start":
                    tool_name = event.get("name", "unknown_tool")
                    tool_input = event.get("data", {})

                    tool_display_name = {
                        "add_product": "Adding Product",
                        "update_product": "Updating Product",
                        "deleteProduct" : "Deleting Product",
                        "getAllProduct" : "Fetching all Products"

                    }

                    display_name = tool_display_name.get(tool_name, tool_name)
                    tool_data= {
                        "type": "tool_call",
                        "tool": tool_name,
                        "display_name": display_name,
                        "input": tool_input
                    }

                    tool_log.append(tool_data)
                    structured_response.append(tool_data)
                    yield f"{json.dumps(tool_data)}\n\n"

                if kind == "on_tool_end":
                    tool_name = event.get("name", "unknown_tool")
                    output = event.get("data", {}).get("output", "")

                    if hasattr(output, "content"):
                        result_output = output.content
                    else:
                        result_output = str(output)

                    tool_result_data = {
                        "type": "tool_result",
                        "tool": tool_name,
                        "content": result_output
                    }
                    structured_response.append(tool_result_data)
                    yield f"{json.dumps(tool_result_data)}\n\n "


                # Extract tokens from agent event
                if kind == "on_chat_model_stream":
                    content = event.get("data", {}).get("chunk", {})
                    if hasattr(content, "content") and content.content:
                        token = content.content
                        full_response += token

                        text_data = {
                            "type": "text",
                            "content": token
                        }
                        yield f"{json.dumps(text_data)}\n\n"

                if kind == "on_chat_model_end":
                    usage = event.get("data", {}).get("output", {})
                    if hasattr(usage, "usage_metadata") and usage.usage_metadata:
                        prompt_tokens += usage.usage_metadata.get("input_tokens", 0)
                        completion_tokens += usage.usage_metadata.get("output_tokens", 0)
                        total_tokens += usage.usage_metadata.get("total_tokens", 0)

        # ---------- SAVE FINAL AI MESSAGE ----------
            if full_response:
                structured_response.append({
                    "type": "text",
                    "content": full_response,
                })
                agent_msg = Message(
                    thread_id=thread_id,
                    role="assistant",
                    content=json.dumps(structured_response),
                    tool_calls = tool_log if tool_log else None,
                    prompt_tokens = prompt_tokens,
                    completion_tokens = completion_tokens,
                    total_tokens = total_tokens,
                )

                db.add(agent_msg)
                db.commit()
                db.refresh(agent_msg)

                message_id_data = {
                    "type" : "message_id",
                    "message_id" : agent_msg.id
                }
                yield f"{json.dumps(message_id_data)}\n\n"



        except SQLAlchemyError:
            print(f"Database error: {e}")
            db.rollback()
            yield "data: ERROR\n\n"
        except Exception as e:
            print(f"General error: {e}")
            traceback.print_exc()
            yield "data: ERROR\n\n"
    
    return EventSourceResponse(event_generator())
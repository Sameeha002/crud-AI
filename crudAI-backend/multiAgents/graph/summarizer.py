# Add to multi_agent_graph.py
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage
import os
from dotenv import load_dotenv

load_dotenv()

summarizer_llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))

def run_summarizer(state: dict):
    """Combines all agent responses into one final reply."""
    messages = state["messages"]
    
    response = summarizer_llm.invoke([
        SystemMessage(content="""You are a final response formatter for a multi-agent customer support system.

Your ONLY job is to read the conversation history and write one clean, friendly response to the user.

STRICT RULES:
- Do NOT call any tools
- Do NOT generate function tags like <function=...> or JSON tool calls
- Do NOT mention agent names, routing, or internal system details
- Do NOT say things like "another agent handled this" or "CONVERSATION Agent", "RESPONSE_FORMATTER" "RESPONSE_FORMATTER"
- ONLY summarize what was actually retrieved — do not make up data

FORMATTING RULES:

For invoices, always format as a table:
| Invoice # | Date       | Total  |
|-----------|------------|--------|
| 391       | 2025-09-20 | $0.99  |
| 339       | 2025-01-30 | $5.94  |

For albums/tracks, format as a numbered list:
1. For Those About To Rock We Salute You
2. Let There Be Rock

For combined results (both invoices + music), present invoices first, then music — with a clear heading for each section.

TONE:
- Friendly and professional
- Address the user directly (e.g. "Here are your invoices")
- Keep it concise — no unnecessary filler sentences"""),
    ] + messages)
    
    return {"messages": [AIMessage(content=response.content)]}
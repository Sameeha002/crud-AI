from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from dotenv import load_dotenv
from ..prompts import SUPERVISOR_PROMPT
import os

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

def needs_music_agent(messages: list) -> bool:
    """Check if the original user query mentions music/albums/artists."""
    for m in messages:
        if isinstance(m, HumanMessage):
            content = m.content.lower()
            if any(word in content for word in ["album", "artist", "track", "song", "music", "ac/dc", "genre"]):
                return True
    return False

def needs_sales_agent(messages: list) -> bool:
    """Check if the original user query mentions invoices/sales."""
    for m in messages:
        if isinstance(m, HumanMessage):
            content = m.content.lower()
            if any(word in content for word in ["invoice", "order", "sales", "customer", "billing", "purchase"]):
                return True
    return False

def run_supervisor(state: dict) -> dict:
    messages = state["messages"]
    completed = state.get("completed_agents", [])

    # Determine what the query needs
    needs_music = needs_music_agent(messages)
    needs_sales = needs_sales_agent(messages)

    # Route to sales first if needed and not done
    if needs_sales and "sales_agent" not in completed:
        next_agent = "sales_agent"

    # Then route to music if needed and not done
    elif needs_music and "music_agent" not in completed:
        next_agent = "music_agent"

    # Everything done
    else:
        next_agent = "FINISH"

    print(f"Supervisor routed to: {next_agent} | Completed: {completed}")

    return {
        "next_agent": next_agent,
        "messages": [AIMessage(content=f"__routed_to__{next_agent}")]
    }
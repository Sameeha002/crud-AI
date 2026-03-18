from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from ..prompts import SUPERVISOR_PROMPT
import os

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

def run_supervisor(state: dict):
    """
    Supervisor node — reads user query and decides which agent to route to.
    Returns updated state with next_agent set.
    """
    messages = state["messages"]
    response = llm.invoke(
        [SystemMessage(content=SUPERVISOR_PROMPT)] + messages
    )
    next_agent = response.content.strip().lower()

    if next_agent not in ["music_agent", "sales_agent"]:
        next_agent = "music_agent"

    print(f"Supervisor routed to: {next_agent}")  

    return {"next_agent": next_agent}
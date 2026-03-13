# agents/music_agent.py
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from tools.chinook_tools import music_tools
from prompts import SALES_AGENT_PROMPT
import os
from langchain_core.messages import SystemMessage

load_dotenv()

# Initialize Groq LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# Create music agent with tools and system prompt
sales_agent = create_react_agent(
    model=llm,
    tools=music_tools,
    prompt= SystemMessage(content=SALES_AGENT_PROMPT)
)


def run_sales_agent(state: dict):
    """
    Entry point for sales agent — called by LangGraph supervisor.
    Receives state, runs agent, returns updated messages.
    """
    result = sales_agent.invoke(state)
    return {"messages": result["messages"]}
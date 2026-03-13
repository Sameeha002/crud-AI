# test_agent.py
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from graph.multi_agent_graph import graph

def test_query(query: str):
    print(f"\n{'='*50}")
    print(f"Query: {query}")
    print(f"{'='*50}")
    
    result = graph.invoke(
        {"messages": [HumanMessage(content=query)]},
        config={"configurable": {"thread_id": "test-1"}}
    )
    
    # Print final response
    final_message = result["messages"][-1]
    print(f"Response: {final_message.content}")

# Test music queries
test_query("Show me albums by AC/DC")
# test_query("Get invoices for customer Mark")

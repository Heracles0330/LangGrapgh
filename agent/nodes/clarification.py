from agent.state import AgentState
from langchain_core.messages import HumanMessage
from langgraph.types import interrupt

def clarification(state: AgentState) -> AgentState:
    user_query = interrupt({"message": state['suggested_clarifying_question'],"type":"clarification"})["data"]
    return {
        **state,
        "query": user_query,
        "needs_clarification": False
    }
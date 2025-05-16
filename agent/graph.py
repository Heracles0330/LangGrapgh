from typing import Literal
from agent.state import AgentState
from langgraph.graph import StateGraph, END
from agent.nodes.clarification import clarification
from agent.nodes.understanding import query_understanding
from agent.nodes.planning import planning
from agent.nodes.reasoning import reasoning
from agent.tool_nodes.mongo_search import mongo_search
from agent.tool_nodes.pinecone_search import pinecone_search
from agent.tool_nodes.web_search import web_search
from agent.nodes.response import response
from langgraph.checkpoint.memory import InMemorySaver

def create_agent_graph():
    memory = InMemorySaver()
    workflow = StateGraph(AgentState)

    workflow.add_node("query_understanding", query_understanding)
    workflow.add_node("clarification", clarification)
    workflow.add_node("planning", planning)
    workflow.add_node("reasoning", reasoning)
    workflow.add_node("mongo_search", mongo_search)
    workflow.add_node("pinecone_search", pinecone_search)
    workflow.add_node("aggregator", aggregate_search_results)
# Create a branch node for parallel execution of MongoDB and Pinecone searches
    workflow.add_node("parallel_search",parallel_search)
    workflow.add_node("web_search",web_search)

    workflow.add_node("response",response)

    workflow.set_entry_point("query_understanding")
    
    def needs_clarification_router(state: AgentState) -> Literal["clarification", "planning"]:
        return "clarification" if state["needs_clarification"] else "planning"

    workflow.add_conditional_edges(
        "query_understanding",
        needs_clarification_router,
        {"clarification": "clarification", "planning": "planning"}
    )

    workflow.add_edge("clarification", "query_understanding")
    workflow.add_edge("planning", "reasoning")
    
    # After reasoning, route to appropriate search tools or END
    def search_router(state: AgentState) -> Literal["search", "response","web_search"]:
        # If this is the second run of reasoning (after search)
        if state.get("is_database_searched", False):
            # If results are sufficient, go to END
            if state.get("is_result_sufficient", False):
                return "response"
            # If results are not sufficient but web search is needed
            elif state.get("needs_web_search", False):
                # We'll let the interrupt in the reasoning node handle the web search question
                return "web_search"
            else:
                return "response"
        # If this is the first run (before search), go to search
        return "search"
    
    workflow.add_conditional_edges(
        "reasoning",
        search_router,
        {
            "search": "parallel_search",
            "web_search": "web_search",
            "response": "response"
        }
    )
    
    
    
    workflow.add_edge("parallel_search", "mongo_search")
    workflow.add_edge("parallel_search", "pinecone_search")
    workflow.add_edge("mongo_search", "aggregator")
    workflow.add_edge("pinecone_search", "aggregator")
    # After aggregating results, go back to reasoning to analyze results
    workflow.add_edge("aggregator", "reasoning")
    workflow.add_edge("web_search", "response")
    workflow.add_edge("response", END)
    return workflow.compile(checkpointer=memory)

def aggregate_search_results(state: AgentState) -> AgentState:
    """Aggregate results from MongoDB and Pinecone searches"""
    # In a real implementation, you would process and format the search results
    # print("#########################")
    mongo_results = state.get("mongo_results", [])
    pinecone_results = state.get("pinecone_results", [])
    searched_result = mongo_results + pinecone_results
    # print(mongo_results, pinecone_results, searched_result)
    # Create a new state with is_database_searched set to True
    new_state = {**state}
    new_state["is_database_searched"] = True
    new_state["searched_result"] = searched_result
    new_state["mongo_results"] = []
    new_state["pinecone_results"] = []
    # For demonstration, we're assuming the search results are already in proper format
    # In a real scenario, you might need to transform them
    
    return new_state
def parallel_search(state: AgentState) -> AgentState:
    """Execute MongoDB and Pinecone searches in parallel"""
    return state
agent_graph = create_agent_graph()
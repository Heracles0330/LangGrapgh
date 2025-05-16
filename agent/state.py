from typing import Dict, List, Any, TypedDict, Optional, Union,Annotated
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict, total=False):
    """The state of the cheese shopping agent with improved reasoning architecture."""
    # Core conversation state
    messages: List[BaseMessage]  # Chat history
    query: str  # Current user query
    needs_clarification: bool  # Whether clarification is needed
    reason: str  # Reason for needing clarification
    suggested_clarifying_question: str  # Suggested clarifying question
    plan: List[str]  # Plan for the agent
    
    # Reasoning and search state
    thought: List[str]  # List of reasoning thoughts
    is_database_searched: bool  # Whether database search has been performed
    searched_result: Dict[str, Any]  # Results from database searches
    pinecone_results:Annotated[List[Any], operator.add]  # Results from Pinecone search
    mongo_results:Annotated[List[Any], operator.add]  # Results from MongoDB search
    # Search query state
    mongo_query: str  # MongoDB query string
    pinecone_query: str  # Pinecone query string
    
    # Result analysis state
    is_result_sufficient: bool  # Whether search results are sufficient
    needs_web_search: bool  # Whether web search is needed
    web_search_query: str  # Web search query
    web_search_results:Dict[str,Any]  # Results from web search

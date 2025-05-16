from langchain_tavily import TavilySearch

from agent.state import AgentState
from dotenv import load_dotenv
import os
load_dotenv()
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
def web_search(state: AgentState) -> AgentState:
    tool = TavilySearch(
        max_results=5,
        topic="general",
        include_answer=True,
        include_raw_content=True,
        include_images=True,
        # include_image_descriptions=True,
        # search_depth="basic",
        # time_range="day",
        # include_domains=None,
        # exclude_domains=None
        
    )
    web_search_results = tool.invoke(state["web_search_query"])
    print(web_search_results)
    return {"web_search_results": web_search_results}
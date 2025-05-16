from agent.state import AgentState
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage,SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini",openai_api_key=os.getenv("OPENAI_API_KEY"))

# Define the prompt template
RESPONSE_PROMPT_TEMPLATE = """
You are a helpful AI assistant for a {app_name}. Your goal is to provide a comprehensive and user-friendly answer based on the user's query and the information gathered from database searches and web searches.

User's Query:
{user_query}

Information from Database Search (e.g., product details, inventory):
{database_results}

Information from Web Search (e.g., articles, reviews, general knowledge, images):
{web_results}

**Instructions for your response:**
1.  Synthesize all the provided information to answer the user's query.
2.  Format your response using Markdown. This will be displayed in a Streamlit application.
3.  If you have relevant image URLs from the web search results (e.g., in a field like 'image_url' or if a link itself is an image), embed them naturally within your response using Markdown: `![Descriptive Alt Text](image_url)`. Choose representative images if multiple are available.
4.  If there are multiple pieces of information, structure your response clearly (e.g., using bullet points or paragraphs).
5.  If the information is conflicting or insufficient to fully answer, acknowledge that and provide the best possible answer with the available data.
6.  Keep the tone conversational and helpful.
7.  Do not make up information. Only use what's provided in the search results.
8.  If no relevant information is found in either database or web searches, inform the user politely that you couldn't find the information.
9.  If there are so many products, don't show all of them. Show only the first 10 products and the total number of products.
Always say the total number of results in the response.
And please show the products in the streamlit markdown format. And show the products in the table format.
Begin your response:
"""

def response(state: AgentState) -> AgentState:
    """
    Generates the final AI response for the user based on aggregated search results.
    """
    user_query = state.get("query", "")
    database_results = state.get("searched_result", {}) # This is from your aggregate_search_results
    web_results = state.get("web_search_results", [])

    # Basic error handling or empty state
    if not user_query:
        return {"final_response": "I didn't receive a query. How can I help you?"}

    prompt = [
        SystemMessage(content=RESPONSE_PROMPT_TEMPLATE.format(
            app_name="Cheese Shopping Assistant", # Or your app's actual name
            user_query=user_query,
            database_results=database_results,
            web_results=web_results
        )),
        HumanMessage(content=f"Please generate a response for my query: {user_query}")
    ]

    ai_response = llm.invoke(prompt)
    print(ai_response.content)
    final_response = ai_response.content
    messages = state["messages"] + [AIMessage(content=ai_response.content)]
    return {"messages":messages, "final_response":final_response}

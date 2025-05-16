import json
from agent.state import AgentState
from langchain_core.messages import HumanMessage
from langgraph.types import interrupt
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini",openai_api_key=os.getenv("OPENAI_API_KEY"))
class LLMOutput(BaseModel):
    needs_clarification: bool
    reason: str
    suggested_clarifying_question: str

query_prompt = ChatPromptTemplate.from_template("""
You are the understanding component of a cheese product chatbot, behaving like a professional cheese sales expert.
Your primary role is to determine if a user's query is understandable and actionable for the subsequent planning and reasoning steps. These steps may include database searches for specific product information or web searches for general knowledge.

User query: {user_query}
History: {history}

First, understand the query in the context of the history and regenerate the complete query if necessary.

Your database ONLY contains these specific fields about cheese products:
- name: Product name
- brand: Brand name
- department: Cheese category
- weights: Available weights
- prices: Price information
- pricePer: Price per unit
- sku: Product ID
- discount: Any discount information
- popularityOrder: Popularity ranking
- priceOrder: Price ranking
- itemCounts, dimensions, images, relateds, empty, href: Other product details

Information NOT in the database (and may require a web search by a later component) includes:
- Country of origin or nationality information (French, Italian, etc.)
- Nutritional information or ingredients
- Flavor profiles or tasting notes
- Production methods or aging information
- Historical information about cheese
- Recipes or cooking recommendations
- Subjective opinions or general cheese knowledge not tied to specific product inventory.

A query `needs_clarification` is true and you should provide a `suggested_clarifying_question` ONLY IF:
1.  It's a simple greeting (e.g., "hello", "how are you?"). In this case, respond politely and ask how you can assist with cheese.
2.  It's completely unrelated to cheese, our products, or food/shopping in general (e.g., "what's the capital of France?", "tell me about cars"). In this case, politely state you can only help with cheese-related queries.
3.  It's excessively vague and provides no clear intent for the chatbot to act upon (e.g., "info", "do something", "help"). In this case, ask for more specifics about what they are looking for regarding cheese or our products.

For all other queries, including general questions about cheese types, origins, recipes, or pairings not in the database, set `needs_clarification` to `false`. These queries are considered understandable, and a downstream 'reasoning' component will decide if a database search or web search is appropriate.

Respond with a JSON object in this exact format:
{{
  "needs_clarification": true/false,
  "reason": "Brief explanation for your decision. If false, indicate why it can proceed (e.g., 'Query is specific to database fields.', 'Query is a general cheese question for web search.').",
  "suggested_clarifying_question": "question (only if needs_clarification is true, otherwise empty string)"
}}

Example of a query that DOES NOT need clarification at this stage:
User Query: "Tell me about French cheese"
LLM Output: {{\"needs_clarification\": false, \"reason\": \"Query is a general cheese topic, potentially answerable by web search.\", \"suggested_clarifying_question\": \"\"}}

Example of a query that DOES need clarification:
User Query: "Hi there!"
LLM Output: {{\"needs_clarification\": true, \"reason\": \"User provided a greeting.\", \"suggested_clarifying_question\": \"Hello! How can I help you with our cheese products today?\"}}

Example of a query that IS specific enough for the database:
User Query: "Do you have cheddar cheese?"
LLM Output: {{\"needs_clarification\": false, \"reason\": \"Query is specific and relates to product inventory.\", \"suggested_clarifying_question\": \"\"}}

Note: Be professional and knowledgeable like a cheese sales expert.
""")

def query_understanding(state: AgentState) -> AgentState:
    
    user_query = state["query"]
    # print(state)
    if "messages" in state.keys():
        prompt = query_prompt.invoke({"user_query": user_query, "history": state["messages"]})
        messages = state["messages"] + [HumanMessage(content=user_query)]
    else:
        prompt = query_prompt.invoke({"user_query": user_query, "history": []})
        messages = [HumanMessage(content=user_query)]
    response = llm.with_structured_output(LLMOutput).invoke(prompt)

    result = response
    
    return {
        **state,
        "messages": messages,
        "query": user_query,
        "needs_clarification": result.needs_clarification,
        "reason": result.reason,
        "suggested_clarifying_question": result.suggested_clarifying_question
    }
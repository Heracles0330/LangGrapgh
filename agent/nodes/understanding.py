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

User query: {user_query}
History: {history}

The user asks based on the previous conversations, so first understand the query in context of the history and regenerate the complete query.

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

Your database DOES NOT contain:
- Country of origin or nationality information (French, Italian, etc.)
- Nutritional information or ingredients
- Flavor profiles or tasting notes
- Production methods or aging information
- Historical information about cheese
- Recipes or cooking recommendations

A regenerated query needs clarification if:
- It's a greeting
- It's asking for information NOT in the database (like nationality, nutrition, etc.)
- It's asking for subjective opinions or general cheese knowledge
- It's not related to our cheese product inventory

Respond with a JSON object in this exact format:
{{
  "needs_clarification": true/false,
  "reason": "Brief explanation of why",
  "suggested_clarifying_question": "question"
}}

When information is not in your database (like nationality), do NOT ask for more specifics about that topic. Instead, explain that you don't have that specific information and redirect to what you can provide.

Example:
For "Tell me about French cheese" → Don't ask "Which French cheese?" 
Instead say: "I don't have information about cheese by country of origin. Would you like to know about available brands, prices, or popular cheese products instead?"

Note: Only include suggested_clarifying_question if needs_clarification is true. Be professional and knowledgeable like a cheese sales expert.
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
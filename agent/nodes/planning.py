import json
from agent.state import AgentState
from langchain_core.messages import HumanMessage
from langgraph.types import interrupt
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini",openai_api_key=os.getenv("OPENAI_API_KEY"))

# Define the prompt template for high-level planning
planning_prompt = ChatPromptTemplate.from_template("""
You are a cheese expert assistant tasked with creating a plan to help the user find the best cheese products.

User query history: {query}
Cheese example: {cheese_example}
First, analyze what the user is looking for (cheese type, preferences, criteria, etc).
Then, create a step-by-step plan to address their needs.

Prioritize direct database access using MongoDB search rather than semantic search methods. Examples of database queries include questions about:
- Inventory counts ("How many cheeses do you have?")
- Price information ("What's the most expensive cheese?")
- Attribute filtering ("Show me all French cheeses")
- Aggregation queries ("What's the average price of your soft cheeses?")

Your plan should include steps such as:
1. Search for relevant cheese products (specify whether to use MongoDB structured search, vector search, or web search)
2. Filter and analyze the products based on specific criteria
3. Generate recommendations or comparisons
4. Any additional steps needed to fully address the query
**Note: If the query is a database query, prioritize MongoDB search over other search methods.**
**Note: If the query is not a database query, prioritize web search over other search methods.**
And there is one important thing you must consider. my server is not so good. So I have to priotize the response time. So if you can reduce the steps, do it.
For example, if the user is asking the number of sliced cheese, you don't need to search for the sliced cheese. You can just count the number using the correct mongoDB query.
And user asks about only name and picture url and brand and etc, you don't need to break the steps into many steps such as finding all fields and filtering criteria. You can just return the result using one correct mongoDB query .
In short reduce the steps as much as possible.
Output a JSON with the following format to directly parse the output using "json.loads(response.content)":
{{"plan": ["Step 1: description", "Step 2: description", ...]}}
for example:
{{"plan": ["Step 1: Search for cheese products matching the query", "Step 2: Analyze and filter the search results", "Step 3: Generate recommendations based on filtered results"]}}
""")
cheese_example = {
    "showImage": "https://d3tlizm80tjdt4.cloudfront.net/image/15196/image/sm-af4d520ed6ba1c0a2c2dbddaffd35ce4.png",
    "name": "Cheese, American, 120 Slice, Yellow, (4) 5 Lb - 103674",
    "brand": "Schreiber",
    "department": "Sliced Cheese",
    "itemCounts": {
      "CASE": 4,
      "EACH": 1
    },
    "dimensions": {
      "CASE": "L 1\" x W 1\" x H 1\"",
      "EACH": "L 1\" x W 1\" x H 1\""
    },
    "weights": {
      "CASE": 5.15,
      "EACH": 1.2875
    },
    "images": [
      "https://d3tlizm80tjdt4.cloudfront.net/image/15196/image/sm-af4d520ed6ba1c0a2c2dbddaffd35ce4.png"
    ],
    "relateds": [
      "100014"
    ],
    "prices": {
      "Case": 67.04,
      "Each": 16.76
    },
    "pricePer": 3.35,
    "sku": "103674",
    "discount": "",
    "empty": False,
    "href": "https://shop.kimelo.com/sku/cheese-american-120-slice-yellow-4-5-lb-103674/103674",
    "priceOrder": 83,
    "popularityOrder": 2
  }
def planning(state: AgentState) -> AgentState:
    query = state["query"]
    prompt = planning_prompt.invoke({"query": state["messages"], "cheese_example": cheese_example})
    response = llm.invoke(prompt)
    state["plan"] = json.loads(response.content)["plan"]
    return state

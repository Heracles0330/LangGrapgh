from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel
from agent.state import AgentState
from langgraph.types import interrupt
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()
llm = init_chat_model("gpt-4o-mini",openai_api_key=os.getenv("OPENAI_API_KEY"))
class LLMOutput(BaseModel):
    thought: str
    is_result_sufficient: bool
    needs_web_search: bool
    mongo_query: str
    pinecone_query: str
    web_search_query: str
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

reasoning_prompt = ChatPromptTemplate.from_template("""
You are a reasoning component of a cheese product search system. Your task is to analyze a user query and either generate search queries or analyze search results.

User query: {user_query}
History: {history}
Is database search already performed: {is_database_searched}
Search results: {searched_result}
Example cheese data schema: {cheese_example}

Your system has three search capabilities:
1. MongoDB Aggregation Pipeline(structured data search) - for specific attribute filtering, counting, and factual queries
2. Pinecone (vector/semantic search) - for similarity and conceptual searches
3. Web search - for general information not in our database

Available MongoDB fields:
- name: Product name 
- brand: Brand name
- department(category): Cheese category (like "Sliced Cheese")
- weights: Available weights
- prices: Price information (Case and Each)
- pricePer: Price per unit
- sku: Product ID
- discount: Any discount information
- popularityOrder: Popularity ranking
- priceOrder: Price ranking
- itemCounts, dimensions, images, relateds, empty, href: Other product details

### PHASE 1: If database search has NOT been performed yet (is_database_searched = false)
Generate appropriate MongoDB and Pinecone queries to answer the user's question.
In this phase:
- Set is_result_sufficient = false (as we don't have results yet)
- Set needs_web_search = false (we'll determine this after getting search results)
- Generate detailed MongoDB aggregation pipeline and Pinecone queries to answer the user's question based on the example cheese data schema. The MongoDB query is for detailed information about the product. The Pinecone query is for a conceptual search. If the pinecone query is not necessary, make them empty string "".As possible as you can, don't user the pinecone query.
- As default the normal price is the each price and if there is no requirement about the data fields, only search for the name,brand,department(category),price,sku,href,images.
- And the department is also the category of the cheese.
- Always don't search the _id field and sort by the price.(set the _id project to 0 and sort by the price)
- Always don't search the _id field and sort by the price.(set the _id project to 0 and sort by the price)
- If the user asks about the previous conversation, identify the product sku and use the sku to search the database because the sku is the unique identifier of the product.
                                                    
### PHASE 2: If search has been performed (is_searched = true)
Analyze the search results to determine if they are sufficient to answer the user's question.
In this phase:
- If results are sufficient: Set is_result_sufficient = true, needs_web_search = false
- If results are NOT sufficient: Set is_result_sufficient = false, needs_web_search = true, and generate an appropriate web_search_query
But I think web search is so slow,so if there is some results, don't suggest web search.
Respond with a JSON object in this format:
{{
  "thought": "Your step-by-step reasoning about the query and search strategy",
  "is_result_sufficient": true/false,
  "needs_web_search": true/false,
  "mongo_query": "MongoDB aggregation pipeline in JSON format so that be abel to json.loads(mongo_query)",
  "pinecone_query": "Search term for Pinecone",
  "web_search_query": "Query for web search if needed"
}}
For MongoDB, use proper query operators like $eq, $gt, $lt, $in, $regex, etc. For complex queries, use aggregation pipeline.

**VERY IMPORTANT for `mongo_query`:**
- Always don't search the _id field and sort by the price.(set the _id project to 0 and sort by the price)
- The entire `mongo_query` string MUST be a valid JSON array of pipeline stages.
- ALL keys (e.g., "$match", "name", "$regex") and ALL string values within the pipeline MUST be enclosed in **double quotes**.
- Example of a correctly formatted `mongo_query` string:
  `"[{{\"$match\": {{\"brand\": \"Schreiber\"}}}}, {{\"$project\": {{\"name\": 1, \"brand\": 1, \"prices.Each\": 1, \"_id\": 0}}}}, {{\"$sort\": {{\"prices.Each\": 1}}}} ]"`
- Do NOT use single quotes for keys or string values.
- Ensure correct escaping if your generated query string itself needs to be embedded in the final JSON output (though the Pydantic model should handle this if the string content is correct).

Avoid syntax like `{{'$match': {{'brand': 'Schreiber'}}}}` as this is invalid.
Only use double quotes: `[{{\"$match\": {{\"brand\": \"Schreiber\"}}}}]`

""")


def reasoning(state: AgentState) -> AgentState:
    is_database_searched = state.get("is_database_searched", False)
    
    prompt = reasoning_prompt.invoke({
        "user_query": state["query"], 
        "history": state["messages"][:-1],
        "is_database_searched": is_database_searched,
        "searched_result": state.get("searched_result", {}),
        "cheese_example": cheese_example
    })
    
    response = llm.with_structured_output(LLMOutput).invoke(prompt)
    
    # Add new thought to existing thoughts list
    if "thought" not in state:
        state["thought"] = []
    
    new_state = {**state}
    new_state["thought"] = state["thought"] + [response.thought]
    new_state["is_result_sufficient"] = response.is_result_sufficient
    new_state["needs_web_search"] = response.needs_web_search
    new_state["mongo_query"] = response.mongo_query
    new_state["pinecone_query"] = response.pinecone_query
    new_state["web_search_query"] = response.web_search_query
    new_state["mongo_results"] = []
    new_state["pinecone_results"] = []
    print(new_state)
    # If results are not sufficient and web search is needed, interrupt for user confirmation
    if (not response.is_result_sufficient) and response.needs_web_search:
        choice = interrupt({"message":f"I need additional information from the web to answer your query. Would you like me to perform a web search for '{response.web_search_query}'? (yes/no)","type":"web_search"})
        if choice["data"] == "yes":
            new_state["needs_web_search"] = True
        else:
            new_state["needs_web_search"] = False
    
    return new_state


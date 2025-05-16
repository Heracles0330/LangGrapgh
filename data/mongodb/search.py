from typing import Dict, List, Any, Optional
from data.mongodb.connection import get_collection
import re
import json

def extract_search_filters(query: str) -> Dict[str, Any]:
    """
    Extract potential filters from a user query.
    
    Args:
        query: The user query string
        
    Returns:
        Dictionary of filter criteria
    """
    filters = {}
    
    # Check for price filters
    price_pattern = r"under\s+\$?(\d+)"
    price_match = re.search(price_pattern, query.lower())
    if price_match:
        price_limit = int(price_match.group(1))
        filters["price_each"] = {"$lte": price_limit}
    
    # Check for milk type
    if "cow" in query.lower():
        filters["milk_type"] = "cow"
    elif "goat" in query.lower():
        filters["milk_type"] = "goat"
    elif "sheep" in query.lower():
        filters["milk_type"] = "sheep"
    
    # Check for texture
    if "soft" in query.lower():
        filters["texture"] = "soft"
    elif "semi-soft" in query.lower() or "semi soft" in query.lower():
        filters["texture"] = "semi-soft"
    elif "hard" in query.lower():
        filters["texture"] = "hard"
    elif "crumbly" in query.lower():
        filters["texture"] = "crumbly"
    
    # Check for specific cheese types
    cheese_types = ["blue", "cheddar", "brie", "gouda", "feta", "mozzarella", "parmesan"]
    for cheese in cheese_types:
        if cheese in query.lower():
            filters["name"] = {"$regex": cheese, "$options": "i"}
    
    return filters

def search_products(query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for cheese products in MongoDB using text search and optional filters.
    
    Args:
        query: The search query
        filters: Optional additional filters to apply
        limit: Maximum number of results to return
        
    Returns:
        List of matching cheese products
    """
    try:
        # Get database connection
        
        collection = get_collection()
        
        # Extract filters from the query if none were provided
        if not filters:
            filters = extract_search_filters(query)
        
        # Prepare the search query
        search_query = {}
        
        # Add text search if query isn't just filter terms
        stripped_query = re.sub(r'(under\s+\$?\d+|cow|goat|sheep|soft|hard|semi-soft|semi soft|crumbly)', '', query).strip()
        if stripped_query:
            # Use text search if available, otherwise fallback to regex
            try:
                search_query["$text"] = {"$search": stripped_query}
            except:
                # Fallback to regex search on name and description
                search_query["$or"] = [
                    {"name": {"$regex": stripped_query, "$options": "i"}},
                    {"description": {"$regex": stripped_query, "$options": "i"}}
                ]
        
        # Combine text search with filters
        if filters:
            final_query = {"$and": [search_query, filters]} if search_query else filters
        else:
            final_query = search_query
        
        # If query is empty, get all products
        if not final_query:
            results = list(collection.find().limit(limit))
        else:
            results = list(collection.find(final_query).limit(limit))
        
        # Convert ObjectId to string for JSON serialization
        for result in results:
            if "_id" in result:
                result["_id"] = str(result["_id"])
        
        return results
    
    except Exception as e:
        print(f"Error searching MongoDB: {str(e)}")
        # Fallback to local JSON data if MongoDB fails
        try:
            with open("data/cheese_data_numeric.json", "r") as f:
                all_products = json.load(f)
            
            # Simple filtering for fallback
            filtered_products = []
            for product in all_products:
                # Basic text matching
                if stripped_query.lower() in product.get("name", "").lower() or stripped_query.lower() in product.get("description", "").lower():
                    if len(filtered_products) < limit:
                        filtered_products.append(product)
            
            return filtered_products[:limit]
        except:
            return [] 
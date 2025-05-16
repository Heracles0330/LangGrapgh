import os
import json
from pathlib import Path
from data.mongodb.schemas import import_products_to_mongodb
from data.pinecone.index import index_cheese_products

# Google Drive file ID for the pre-scraped data
GDRIVE_FILE_ID = "13HNQaUwNdOjdcjNtz-Yf-7l-yqH0UKJT"
DATA_PATH = Path("data/cheese_data.json")


def process_and_store_data():
    """Process the cheese data and store it in MongoDB and Pinecone."""
    # Load the data
    cheese_data = json.load(open("data/cheese_data_numeric.json"))
    
    # Import to MongoDB
    import_products_to_mongodb(cheese_data)
    
    # Index in Pinecone
    index_cheese_products(cheese_data)
    
    return cheese_data

if __name__ == "__main__":
    # This allows running the script directly to load data
    process_and_store_data()

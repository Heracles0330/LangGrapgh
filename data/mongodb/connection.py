import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pymongo.server_api import ServerApi
# Load environment variables
load_dotenv()

def get_mongodb_client():
    """Get MongoDB client using connection string from environment variables."""
    connection_string = os.getenv("MONGODB_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("MONGODB_CONNECTION_STRING environment variable not set")
    
    return MongoClient(connection_string)

def get_database(db_name="Cheese"):
    """Get MongoDB database."""
    client = get_mongodb_client()
    return client[db_name]

def get_collection(collection_name="cheese"):
    """Get MongoDB collection."""
    db = get_database()
    return db[collection_name]

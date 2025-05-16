from data.mongodb.connection import get_mongodb_client, get_database, get_collection
import os
from dotenv import load_dotenv

def test_mongodb_connection():
    """Test the MongoDB connection and print connection status."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get the connection string (for display purposes)
        conn_string = os.getenv("MONGODB_CONNECTION_STRING")
        print(f"Using connection string: {conn_string[:20]}..." if conn_string else "No connection string found!")
        
        # Try to connect
        client = get_mongodb_client()
        print("✅ Successfully connected to MongoDB!")
        print(os.getenv("MONGODB_CONNECTION_STRING")) 
        # try:
        #     client.admin.command('ping')
        #     print("Pinged your deployment. You successfully connected to MongoDB!")
        # except Exception as e:
        #     print(e)
                # List available databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")
        
        # Get our database and collection
        db = get_database()
        print(f"Selected database: {db.name}")
        
        # List collections in the database
        collections = db.list_collection_names()
        print(f"Collections in {db.name}: {collections}")
        
        # Check products collection
        products = get_collection()
        count = products.count_documents({})
        print(f"Products collection has {count} documents")
        
        # Get a sample document
        if count > 0:
            sample = products.find_one()
            print("\nSample document:")
            for key, value in sample.items():
                if key != "_id":  # Skip the _id field for cleaner output
                    print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {str(e)}")
        return False

if __name__ == "__main__":
    test_mongodb_connection() 
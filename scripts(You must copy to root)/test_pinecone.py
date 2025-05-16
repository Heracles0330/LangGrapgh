from data.pinecone.connection import init_pinecone, get_index
from data.pinecone.index import pinecone_search
from data.embeddings import get_embedding
import os
from dotenv import load_dotenv
import pinecone
import time

def test_pinecone_connection():
    """Test the Pinecone connection and basic functionality."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get API key for display
        api_key = os.getenv("PINECONE_API_KEY")
        environment = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
        print(f"Using API key: {api_key[:5]}..." if api_key else "No API key found!")
        print(f"Environment: {environment}")
        
        # Initialize Pinecone
        print("\nInitializing Pinecone...")
        pc = init_pinecone()
        
        # List available indexes
        indexes = pc.list_indexes()
        print(f"Available indexes: {indexes}")
        
        # Get our index
        index_name = "cheese-products"
        
        index = get_index(pc, index_name)
        
        # Get index stats
        stats = index.describe_index_stats()
        print(f"Index stats: {stats}")
        
        # Check if there are any vectors
        vector_count = stats["total_vector_count"]
        print(f"Total vectors: {vector_count}")
        
        if vector_count > 0:
            # Perform a sample search
            print("\nPerforming a sample search for 'creamy soft cheese'...")
            results = pinecone_search("creamy soft cheese", top_k=3)
            
            print(f"\nFound {len(results)} results:")
            for i, result in enumerate(results):
                print(f"\n{i+1}. {result.get('name', 'Unknown')} (score: {result.get('score', 0):.4f})")
                print(f"   Price: {result.get('price', 'N/A')}")
                print(f"   Description: {result.get('description', 'N/A')[:100]}...")
        else:
            print("\nNo vectors in the index yet. You may need to run data import first.")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Pinecone: {str(e)}")
        return False

if __name__ == "__main__":
    test_pinecone_connection() 
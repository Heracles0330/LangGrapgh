import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_pinecone():
    """Initialize Pinecone client with API key from environment."""
    api_key = os.getenv("PINECONE_API_KEY")
    environment = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
    
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable not set")
    
    pc = Pinecone(
        api_key=api_key
    )
    print("Pinecone initialized successfully")
    return pc
def get_index(pc, index_name="cheese-products", dimension=1536):
    """Get or create a Pinecone index for cheese products.
    
    Args:
        index_name: Name of the Pinecone index
        dimension: Dimension of the embeddings (1536 for OpenAI)
        
    Returns:
        Pinecone index
    """
    # Initialize Pinecone if not already initialized
    indexes = pc.list_indexes()
    
    # Extract index names from the list of dictionaries
    index_names = [index["name"] for index in indexes]
    
    # Check if index exists, create if it doesn't
    if index_name not in index_names:
        print(f"Creating Pinecone index '{index_name}'...")
        pc.create_index(
            name=index_name,
            metric="cosine",
            dimension=dimension,
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        print(f"Pinecone index '{index_name}' created")
    
    # Return the index
    return pc.Index(index_name)

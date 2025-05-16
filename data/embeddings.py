import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
# Load environment variables
load_dotenv()
def get_embedding(text: str, model="text-embedding-ada-002") -> List[float]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding

def get_batch_embeddings(texts: List[str], model="text-embedding-ada-002", batch_size=100) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts.
    
    Args:
        texts: List of texts to embed
        model: The OpenAI embedding model to use
        batch_size: Maximum number of texts to embed in one API call
        
    Returns:
        List of embedding vectors
    """
    all_embeddings = []
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Process in batches to avoid API limits
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        
        # Clean the texts
        cleaned_batch = [text.strip().replace("\n", " ") for text in batch if isinstance(text, str) and text.strip()]
        
        if not cleaned_batch:
            continue
        # print(cleaned_batch)
        try:
            # Call OpenAI's embedding API
            response = client.embeddings.create(input=cleaned_batch, model=model)
            # Extract embeddings
            batch_embeddings = [item.embedding for item in response.data]
            # print(batch_embeddings)
            all_embeddings.extend(batch_embeddings)
            
            print(f"Generated embeddings for batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
        except Exception as e:
            print(f"Error generating batch embeddings: {str(e)}")
            # Add zero vectors as fallback
            all_embeddings.extend([[0.0] * 1536] * len(cleaned_batch))
    
    return all_embeddings

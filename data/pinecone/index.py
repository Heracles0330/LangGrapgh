from typing import List, Dict, Any
import uuid
from data.pinecone.connection import get_index, init_pinecone
from data.embeddings import get_embedding, get_batch_embeddings

def index_cheese_products(products: List[Dict[str, Any]], batch_size: int = 50):
    """
    Index cheese products in Pinecone.
    
    Args:
        products: List of cheese product dictionaries
        batch_size: Number of products to index in a single batch
    """
    # Get the Pinecone index
    pc = init_pinecone()
    index = get_index(pc)
    
    print(f"Indexing {len(products)} cheese products in Pinecone...")
    
    # Process in batches
    for i in range(0, len(products), batch_size):
        batch = products[i:i+batch_size]
        
        # Prepare product texts for embedding
        product_texts = []
        for product in batch:
            # Concatenate relevant fields for better semantic search
            text = f"{product.get('name', '')} {product.get('brand', '')} "
            text += f"{product.get('department', '')} "
            
            # Add prices if available
            if 'prices' in product and isinstance(product['prices'], dict):
                prices_text = ' '.join([f"{k} ${v}" for k, v in product['prices'].items()])
                text += f"{prices_text} "
            
            # Add weights if available
            if 'weights' in product and isinstance(product['weights'], dict):
                weights_text = ' '.join([f"{k} {v} pounds" for k, v in product['weights'].items()])
                text += f"Weights: {weights_text} "
            
            # Add item counts if available
            if 'itemCounts' in product and isinstance(product['itemCounts'], dict):
                counts_text = ' '.join([f"{k} {v} items" for k, v in product['itemCounts'].items()])
                text += f"Item counts: {counts_text} "
            
            # Add discount if available
            if 'discount' in product and product['discount']:
                text += f"Special offer: {product['discount']} "
            
            # Add related products if available
            if 'relateds' in product and product['relateds']:
                text += f"Related products: {' '.join(product['relateds'])} "
            
            # Add price per unit
            if 'pricePer' in product:
                text += f"Price per unit: ${product['pricePer']} "
            
            # Add product availability
            if 'empty' in product:
                status = "Out of stock" if product['empty'] else "In stock"
                text += f"{status} "
            
            product_texts.append(text)
        
        # Generate embeddings for the batch
        embeddings = get_batch_embeddings(product_texts)
        
        # Prepare vectors for upsert
        vectors = []
        for product, embedding in zip(batch, embeddings):
            # Use SKU as ID if available, otherwise create a UUID
            product_id = product.get('sku', str(uuid.uuid4()))
            
            # Extract relevant metadata for retrieval
            metadata = {
                "name": product.get("name", ""),
                "brand": product.get("brand", ""),
                "department": product.get("department", ""),
                "showImage": product.get("showImage", ""),
                "sku": product.get("sku", ""),
                "pricePer": product.get("pricePer", 0.0),
                "popularityOrder": product.get("popularityOrder", 0),
                "empty": product.get("empty", False)
            }
            
            # Add prices - extract both Each and Case values
            if 'prices' in product:
                metadata["prices_str"] = str(product["prices"])
                
                # Add individual price fields
                if 'Each' in product['prices']:
                    metadata["price_each"] = product['prices']['Each']
                if 'Case' in product['prices']:
                    metadata["price_case"] = product['prices']['Case']
            
            # Add weights - extract both EACH and CASE values
            if 'weights' in product:
                metadata["weights_str"] = str(product["weights"])
                
                # Add individual weight fields
                if 'EACH' in product['weights']:
                    metadata["weight_each"] = product['weights']['EACH']
                if 'CASE' in product['weights']:
                    metadata["weight_case"] = product['weights']['CASE']
            
            # Add item counts - extract both EACH and CASE values
            if 'itemCounts' in product:
                metadata["item_counts_str"] = str(product["itemCounts"])
                
                # Add individual itemCount fields
                if 'EACH' in product['itemCounts']:
                    metadata["count_each"] = product['itemCounts']['EACH']
                if 'CASE' in product['itemCounts']:
                    metadata["count_case"] = product['itemCounts']['CASE']
            
            # Add dimensions if available
            if 'dimensions' in product:
                metadata["dimensions_str"] = str(product["dimensions"])
                if 'EACH' in product['dimensions']:
                    metadata["dimension_each"] = product['dimensions']['EACH']
                if 'CASE' in product['dimensions']:
                    metadata["dimension_case"] = product['dimensions']['CASE']
            
            # Add other fields if they exist
            if "images" in product and product["images"]:
                metadata["images"] = product["images"][0] if product["images"] else ""
                # Store up to 3 additional images if available
                if len(product["images"]) > 1:
                    metadata["additional_images"] = product["images"][1:4]
            
            if "href" in product:
                metadata["href"] = product["href"]
            if "discount" in product:
                metadata["discount"] = product["discount"]
            if "priceOrder" in product:
                metadata["priceOrder"] = product["priceOrder"]
            
            # Create vector record
            # print(embedding)
            vectors.append({
                "id": product_id,
                "values": embedding,
                "metadata": metadata
            })
        
        # Upsert the batch
        if vectors:
            index.upsert(vectors=vectors)
            print(f"Indexed batch {i//batch_size + 1}/{(len(products)-1)//batch_size + 1} ({len(vectors)} products)")
    
    print(f"Successfully indexed {len(products)} cheese products in Pinecone")

def pinecone_search(query: str, top_k: int = 5, filter: Dict = None):
    """
    Search for cheese products in Pinecone using semantic search.
    
    Args:
        query: Search query
        top_k: Number of results to return
        filter: Optional metadata filters
        
    Returns:
        List of matching cheese products with similarity scores
    """
    # Get the Pinecone index
    pc = init_pinecone()
    index = get_index(pc)
    
    # Generate embedding for the query
    query_embedding = get_embedding(query)
    
    # Search in Pinecone
    search_params = {
        "vector": query_embedding,
        "top_k": top_k,
        "include_metadata": True
    }
    
    # Add filter if provided
    if filter:
        search_params["filter"] = filter
    
    # Execute the search
    results = index.query(**search_params)
    
    # Format the results
    products = []
    for match in results.get("matches", []):
        product = {
            "id": match["id"],
            "score": match["score"],
            **match["metadata"]
        }
        products.append(product)
    
    return products

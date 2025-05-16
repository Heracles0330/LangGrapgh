from pymongo import IndexModel, ASCENDING, TEXT
from data.mongodb.connection import get_collection

# Define schema for cheese products based on cheese_data_numeric.json
product_schema = {
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "prices", "brand"],
            "properties": {
                "name": {
                    "bsonType": "string",
                    "description": "Name of the cheese product"
                },
                "showImage": {
                    "bsonType": "string",
                    "description": "Primary image URL for the product"
                },
                "brand": {
                    "bsonType": "string",
                    "description": "Brand of the cheese product"
                },
                "department": {
                    "bsonType": "string",
                    "description": "Department or category the product belongs to"
                },
                "itemCounts": {
                    "bsonType": "object",
                    "description": "Count of items in different packaging units",
                    "additionalProperties": {
                        "bsonType": "int"
                    }
                },
                "dimensions": {
                    "bsonType": "object",
                    "description": "Dimensions of the product in different units",
                    "additionalProperties": {
                        "bsonType": "string"
                    }
                },
                "weights": {
                    "bsonType": "object",
                    "description": "Weight of the product in different units",
                    "additionalProperties": {
                        "bsonType": "double"
                    }
                },
                "images": {
                    "bsonType": "array",
                    "description": "URLs to product images",
                    "items": {
                        "bsonType": "string"
                    }
                },
                "relateds": {
                    "bsonType": "array",
                    "description": "SKUs of related products",
                    "items": {
                        "bsonType": "string"
                    }
                },
                "prices": {
                    "bsonType": "object",
                    "description": "Prices in different units",
                    "additionalProperties": {
                        "bsonType": "double"
                    }
                },
                "pricePer": {
                    "bsonType": "double",
                    "description": "Price per unit (usually per pound)"
                },
                "sku": {
                    "bsonType": "string",
                    "description": "Stock keeping unit identifier"
                },
                "discount": {
                    "bsonType": "string",
                    "description": "Discount information"
                },
                "empty": {
                    "bsonType": "bool",
                    "description": "Whether the product is out of stock"
                },
                "href": {
                    "bsonType": "string",
                    "description": "URL to the product page"
                },
                "priceOrder": {
                    "bsonType": "int",
                    "description": "Ranking by price"
                },
                "popularityOrder": {
                    "bsonType": "int",
                    "description": "Ranking by popularity"
                }
            }
        }
    }
}

def setup_mongodb():
    """Set up MongoDB collections with proper schemas and indexes."""
    # Get products collection
    products = get_collection()
    
    # Create text index for search
    products.create_index([
        ("name", TEXT),
        ("brand", TEXT),
        ("department", TEXT)
    ])
    
    # Create indexes for common queries
    products.create_index([("pricePer", ASCENDING)])
    products.create_index([("brand", ASCENDING)])
    products.create_index([("sku", ASCENDING)])
    products.create_index([("popularityOrder", ASCENDING)])
    products.create_index([("empty", ASCENDING)])
    
    # Return the configured collection
    return products

def import_products_to_mongodb(products_data, clear_existing=True):
    """Import cheese products to MongoDB.
    
    Args:
        products_data: List of dictionaries containing product information
        clear_existing: Whether to clear existing products before import
    """
    products = get_collection()
    
    # Clear existing data if requested
    if clear_existing:
        deleted = products.delete_many({})
        print(f"Cleared {deleted.deleted_count} existing products")
    
    # Insert products
    if len(products_data) > 0:
        products.insert_many(products_data)
        print(f"Imported {len(products_data)} products to MongoDB")
    else:
        print("No products to import")

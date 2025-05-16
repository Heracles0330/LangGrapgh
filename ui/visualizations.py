import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any, Optional
import json

def create_radar_chart(flavor_data: Dict[str, Any]):
    """
    Create a radar chart for flavor profiles.
    
    Args:
        flavor_data: Dictionary with radar chart data
        
    Returns:
        Plotly figure
    """
    # Extract the data
    labels = flavor_data["labels"]
    datasets = flavor_data["datasets"]
    
    # Create the figure
    fig = go.Figure()
    
    # Add each product dataset
    for dataset in datasets:
        fig.add_trace(go.Scatterpolar(
            r=dataset["data"],
            theta=labels,
            fill='toself',
            name=dataset["label"],
            line=dict(color=dataset["borderColor"]),
            fillcolor=dataset["backgroundColor"]
        ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=True,
        title="Flavor Profile Comparison"
    )
    
    return fig

def create_price_bar_chart(products: List[Dict[str, Any]], max_products: int = 5):
    """
    Create a bar chart comparing product prices.
    
    Args:
        products: List of product dictionaries
        max_products: Maximum number of products to include
        
    Returns:
        Plotly figure
    """
    # Prepare data
    names = []
    prices = []
    
    for product in products[:max_products]:
        name = product.get("name", "Unknown")
        # Get price from different possible fields
        price = None
        if "price_each" in product:
            price = product["price_each"]
        elif "price" in product:
            if isinstance(product["price"], (int, float)):
                price = product["price"]
            elif isinstance(product["price"], str):
                # Try to extract numeric price from string
                import re
                match = re.search(r'(\d+\.\d+|\d+)', product["price"])
                if match:
                    price = float(match.group(1))
        
        if price is not None:
            names.append(name[:15] + "..." if len(name) > 15 else name)
            prices.append(price)
    
    if not prices:
        return None
    
    # Create DataFrame
    df = pd.DataFrame({
        "Product": names,
        "Price": prices
    })
    
    # Create bar chart
    fig = px.bar(
        df, 
        x="Product", 
        y="Price", 
        title="Price Comparison",
        labels={"Price": "Price ($)", "Product": ""},
        color_discrete_sequence=["#4CAF50"]
    )
    
    # Update layout
    fig.update_layout(
        xaxis=dict(tickangle=-45),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    
    return fig

def create_product_table(products: List[Dict[str, Any]], max_products: int = 5):
    """
    Create a formatted table of product details.
    
    Args:
        products: List of product dictionaries
        max_products: Maximum number of products to include
        
    Returns:
        Pandas DataFrame
    """
    # Select the fields to display
    fields = [
        "name", "brand", "price", "price_each", "origin", 
        "milk_type", "texture", "flavor_profile"
    ]
    
    # Prepare data
    table_data = []
    
    for product in products[:max_products]:
        row = {}
        for field in fields:
            if field in product:
                # Format value based on field type
                if field == "flavor_profile" and isinstance(product[field], list):
                    row[field] = ", ".join(product[field])
                else:
                    row[field] = product[field]
        table_data.append(row)
    
    if not table_data:
        return None
    
    # Create DataFrame
    df = pd.DataFrame(table_data)
    
    # Rename columns to be more user-friendly
    rename_map = {
        "name": "Product",
        "brand": "Brand",
        "price": "Price",
        "price_each": "Price (Each)",
        "origin": "Origin",
        "milk_type": "Milk Type",
        "texture": "Texture",
        "flavor_profile": "Flavor Profile"
    }
    
    # Apply renaming for columns that exist
    rename_cols = {k: v for k, v in rename_map.items() if k in df.columns}
    if rename_cols:
        df = df.rename(columns=rename_cols)
    
    return df

def create_agent_graph_visualization():
    """
    Create a visualization of the agent's graph structure.
    
    Returns:
        HTML for the graph visualization
    """
    # This is a simplified version - in a real implementation,
    # you would extract the graph structure from the agent
    
    nodes = [
        {"id": "query_understanding", "label": "Query Understanding", "color": "#4CAF50"},
        {"id": "clarification", "label": "Human Clarification", "color": "#2196F3"},
        {"id": "planning", "label": "Planning", "color": "#9C27B0"},
        {"id": "search", "label": "Search Coordinator", "color": "#FF9800"},
        {"id": "tools", "label": "Tool Execution", "color": "#F44336"},
        {"id": "response", "label": "Response Generation", "color": "#3F51B5"}
    ]
    
    edges = [
        {"from": "query_understanding", "to": "clarification", "label": "needs clarification"},
        {"from": "query_understanding", "to": "planning", "label": "clear query"},
        {"from": "clarification", "to": "query_understanding", "label": "user clarified"},
        {"from": "planning", "to": "search", "label": ""},
        {"from": "search", "to": "tools", "label": ""},
        {"from": "tools", "to": "response", "label": ""}
    ]
    
    # Create a vis.js network diagram
    html = f"""
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <div id="agent-graph" style="height: 400px; border: 1px solid #ddd;"></div>
    <script>
        var nodes = new vis.DataSet({json.dumps(nodes)});
        var edges = new vis.DataSet({json.dumps(edges)});
        
        var container = document.getElementById("agent-graph");
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        var options = {{
            nodes: {{
                shape: 'box',
                font: {{
                    size: 16
                }},
                margin: 10
            }},
            edges: {{
                arrows: 'to',
                font: {{
                    size: 12,
                    align: 'middle'
                }}
            }},
            physics: {{
                enabled: true,
                solver: 'forceAtlas2Based'
            }}
        }};
        var network = new vis.Network(container, data, options);
    </script>
    """
    
    return html

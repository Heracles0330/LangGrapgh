import streamlit as st
from typing import Dict, List, Any, Optional, Callable
from old_agent.tools.visualization import generate_product_comparison_data
import pandas as pd

def create_product_selection_widget(products: List[Dict[str, Any]], on_select: Callable):
    """
    Create an interactive product selection widget.
    
    Args:
        products: List of product dictionaries
        on_select: Callback function when a product is selected
    """
    if not products:
        st.info("No products available for selection")
        return
    
    # Create a radio button for product selection
    product_options = [p.get("name", f"Product {i+1}") for i, p in enumerate(products)]
    selected_product_name = st.selectbox("Select a product for details:", product_options)
    
    # Find the selected product
    selected_product = next(
        (p for p in products if p.get("name") == selected_product_name),
        products[0]
    )
    
    # Call the callback with the selected product
    on_select(selected_product)

def create_filter_sidebar(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create interactive filter controls in the sidebar.
    
    Args:
        products: List of product dictionaries
        
    Returns:
        Filtered list of products
    """
    st.sidebar.subheader("🔍 Filter Products")
    
    filtered_products = products.copy()
    
    # Only show filters if we have products
    if not filtered_products:
        st.sidebar.info("No products to filter")
        return filtered_products
    
    # Price filter - find min and max prices
    prices = []
    for product in filtered_products:
        price = None
        if "price_each" in product:
            price = float(product["price_each"])
        elif "price" in product and isinstance(product["price"], (int, float)):
            price = float(product["price"])
        elif "price" in product and isinstance(product["price"], str):
            # Try to extract numeric price from string
            import re
            match = re.search(r'(\d+\.\d+|\d+)', product["price"])
            if match:
                price = float(match.group(1))
        
        if price is not None:
            prices.append(price)
    
    if prices:
        min_price = min(prices)
        max_price = max(prices)
        
        # Create price range slider
        price_range = st.sidebar.slider(
            "Price Range:",
            min_value=float(min_price),
            max_value=float(max_price),
            value=(float(min_price), float(max_price)),
            step=0.5
        )
        
        # Apply price filter
        filtered_products = [
            p for p in filtered_products if (
                ("price_each" in p and price_range[0] <= float(p["price_each"]) <= price_range[1]) or
                ("price" in p and isinstance(p["price"], (int, float)) and price_range[0] <= float(p["price"]) <= price_range[1])
            )
        ]
    
    # Extract unique origins
    origins = set()
    for product in filtered_products:
        if "origin" in product and product["origin"]:
            origins.add(product["origin"])
    
    if origins:
        # Create origin multiselect
        selected_origins = st.sidebar.multiselect(
            "Origin:",
            options=sorted(list(origins)),
            default=[]
        )
        
        # Apply origin filter if selections made
        if selected_origins:
            filtered_products = [
                p for p in filtered_products if (
                    "origin" in p and p["origin"] in selected_origins
                )
            ]
    
    # Extract unique milk types
    milk_types = set()
    for product in filtered_products:
        if "milk_type" in product and product["milk_type"]:
            milk_types.add(product["milk_type"])
    
    if milk_types:
        # Create milk type multiselect
        selected_milk_types = st.sidebar.multiselect(
            "Milk Type:",
            options=sorted(list(milk_types)),
            default=[]
        )
        
        # Apply milk type filter if selections made
        if selected_milk_types:
            filtered_products = [
                p for p in filtered_products if (
                    "milk_type" in p and p["milk_type"] in selected_milk_types
                )
            ]
    
    # Show how many products match the filters
    st.sidebar.info(f"{len(filtered_products)} products match your filters")
    
    return filtered_products

def create_comparison_widget(products: List[Dict[str, Any]], max_products: int = 3):
    """
    Create an interactive product comparison widget.
    
    Args:
        products: List of product dictionaries
        max_products: Maximum number of products to compare
    """
    if not products or len(products) < 2:
        st.info("Need at least 2 products for comparison")
        return
    
    st.subheader("🔍 Compare Products")
    
    # Create multiselect for product selection
    product_options = [(i, p.get("name", f"Product {i+1}")) for i, p in enumerate(products)]
    selected_indices = st.multiselect(
        "Select products to compare:",
        options=product_options,
        format_func=lambda x: x[1],
        default=[product_options[0][0], product_options[1][0]] if len(product_options) > 1 else []
    )
    
    # Limit selections
    if len(selected_indices) > max_products:
        st.warning(f"You can only compare up to {max_products} products at once.")
        selected_indices = selected_indices[:max_products]
    
    # Get selected products
    selected_products = [products[i] for i, _ in selected_indices]
    
    if len(selected_products) < 2:
        st.info("Select at least 2 products to compare")
        return
    
    # Generate comparison data
    comparison_data = generate_product_comparison_data(selected_products)
    
    if "error" in comparison_data:
        st.error(comparison_data["error"])
        return
    
    # Display comparison table
    product_data = comparison_data["products"]
    fields = comparison_data["fields"]
    
    # Create a DataFrame for display
    df_data = {}
    
    # Add fields as rows
    for field in fields:
        field_id = field["id"]
        field_name = field["name"]
        
        # Create a row for this field
        row = []
        for product in product_data:
            if field_id in product:
                row.append(product[field_id])
            else:
                row.append("N/A")
        
        df_data[field_name] = row
    
    # Create column headers (product names)
    product_names = [p.get("name", f"Product {i+1}") for i, p in enumerate(selected_products)]
    
    # Create DataFrame with product names as columns
    df = pd.DataFrame(df_data, index=product_names).transpose()
    
    # Display the table
    st.table(df)

def create_agent_visualization_toggle():
    """Create a toggle for showing/hiding the agent visualization."""
    show_graph = st.checkbox("Show Agent Graph", value=False)
    
    if show_graph:
        from ui.visualizations import create_agent_graph_visualization
        
        # Display the graph visualization
        graph_html = create_agent_graph_visualization()
        st.components.v1.html(graph_html, height=500)

import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any, Optional
from langchain_core.messages import AIMessage, HumanMessage
from old_agent.tools.visualization import (
    generate_product_comparison_data,
    generate_price_chart_data,
    generate_flavor_profile_chart
)
import json

def setup_ui(agent):
    """Set up the main Streamlit UI components."""
    # Set up session state for conversation history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "reasoning_steps" not in st.session_state:
        st.session_state.reasoning_steps = []
    
    if "products" not in st.session_state:
        st.session_state.products = []
    
    # Chat history display
    display_chat_history()
    
    # User input
    user_input = st.chat_input("Ask about cheese...")
    if user_input:
        process_user_input(agent, user_input)

def display_chat_history():
    """Display the chat history."""
    for message in st.session_state.messages:
        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.markdown(message.content)
        else:
            with st.chat_message("assistant"):
                st.markdown(message.content)

def process_user_input(agent, user_input):
    """Process user input and update the UI."""
    # Add user message to chat history
    user_message = HumanMessage(content=user_input)
    st.session_state.messages.append(user_message)
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Show thinking indicator
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("🧠 Thinking...")
        
        # Run the agent
        result = agent.invoke({
            "messages": st.session_state.messages,
            "query": "",
            "needs_clarification": False,
            "products": [],
            "reasoning_steps": [],
            "current_task": "",
            "search_plan": {},
            "search_results": {},
            "final_answer": None
        })
        
        # Update session state with agent results
        st.session_state.reasoning_steps = result.get("reasoning_steps", [])
        st.session_state.products = result.get("products", [])
        
        # Get the AI message from the result
        ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
        if ai_messages:
            ai_message = ai_messages[-1]
            st.session_state.messages.append(ai_message)
            
            # Replace thinking indicator with AI response
            thinking_placeholder.markdown(ai_message.content)
    
    # Display reasoning steps and visualizations in sidebar
    display_reasoning_and_visualizations()

def display_reasoning_and_visualizations():
    """Display reasoning steps and product visualizations in the sidebar."""
    with st.sidebar:
        # Display reasoning steps
        if st.session_state.reasoning_steps:
            st.subheader("💭 Reasoning Steps")
            for i, step in enumerate(st.session_state.reasoning_steps):
                st.markdown(f"{i+1}. {step}")
        
        # Display product visualizations if products are available
        if st.session_state.products:
            st.subheader("🧀 Product Insights")
            
            # Product count
            st.markdown(f"Found {len(st.session_state.products)} cheese products")
            
            # Price comparison chart if there are multiple products
            if len(st.session_state.products) > 1:
                chart_data = generate_price_chart_data(st.session_state.products[:5])
                if "error" not in chart_data:
                    st.subheader("💰 Price Comparison")
                    
                    # Convert to DataFrame for Plotly
                    df = pd.DataFrame({
                        "Product": chart_data["labels"],
                        "Price": chart_data["datasets"][0]["data"]
                    })
                    
                    # Create and display chart
                    fig = px.bar(
                        df, 
                        x="Product", 
                        y="Price", 
                        title="Price Comparison",
                        labels={"Price": "Price ($)", "Product": ""},
                        color_discrete_sequence=["#4CAF50"]
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Product comparison
                st.subheader("🔍 Product Comparison")
                comparison_data = generate_product_comparison_data(st.session_state.products[:3])
                if "error" not in comparison_data:
                    # Convert to a more streamlit-friendly format
                    products = comparison_data["products"]
                    fields = comparison_data["fields"]
                    
                    # Only show the most important fields
                    important_fields = [f for f in fields if f["priority"] < 10]
                    
                    # Create comparison table
                    comparison_df = pd.DataFrame(products)
                    if not comparison_df.empty:
                        # Keep only the columns we want to display
                        display_columns = ["name"] + [f["id"] for f in important_fields if f["id"] != "name"]
                        display_columns = [col for col in display_columns if col in comparison_df.columns]
                        
                        # Rename columns to be more user-friendly
                        rename_map = {f["id"]: f["name"] for f in fields}
                        
                        # Display table
                        st.dataframe(
                            comparison_df[display_columns].rename(columns=rename_map),
                            use_container_width=True
                        )
            
            # Flavor profile visualization if available
            flavor_data = generate_flavor_profile_chart(st.session_state.products[:3])
            if "error" not in flavor_data:
                st.subheader("🌶️ Flavor Profiles")
                
                # Display as radar chart
                # (This is a placeholder - radar charts in Streamlit require some workarounds)
                st.json(flavor_data)
                st.info("Interactive flavor profile chart would be displayed here")

def display_product_details(product: Dict[str, Any]):
    """Display detailed information about a specific product."""
    st.subheader(product.get("name", "Unknown Product"))
    
    # Create columns for layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Display product image if available
        if "image_url" in product:
            st.image(product["image_url"], width=150)
        else:
            st.image("https://via.placeholder.com/150?text=No+Image", width=150)
    
    with col2:
        # Display basic product information
        if "price" in product:
            st.markdown(f"**Price**: {product['price']}")
        elif "price_each" in product:
            st.markdown(f"**Price**: ${product['price_each']}")
        
        if "brand" in product:
            st.markdown(f"**Brand**: {product['brand']}")
        
        if "origin" in product:
            st.markdown(f"**Origin**: {product['origin']}")
        
        if "milk_type" in product:
            st.markdown(f"**Milk Type**: {product['milk_type']}")
    
    # Display description
    if "description" in product and product["description"]:
        st.markdown("### Description")
        st.markdown(product["description"])
    
    # Display detailed specifications
    st.markdown("### Specifications")
    specs = {}
    
    # Add various fields that might be present
    for field in ["texture", "flavor_profile", "aging_time", "weight_each", "popularityOrder"]:
        if field in product and product[field]:
            # Format the field name for display
            display_name = field.replace("_", " ").title()
            # Format the value
            if isinstance(product[field], list):
                value = ", ".join(product[field])
            else:
                value = product[field]
            specs[display_name] = value
    
    # Display as a table
    if specs:
        specs_df = pd.DataFrame(specs.items(), columns=["Attribute", "Value"])
        st.table(specs_df)
    else:
        st.info("No detailed specifications available")
    
    # Display analysis if available
    if "analysis" in product:
        st.markdown("### Expert Analysis")
        st.markdown(product["analysis"])

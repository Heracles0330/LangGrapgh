import streamlit as st
from old_agent.graph import create_agent_graph
from ui.components import setup_ui

st.set_page_config(
    page_title="Cheese Shopping Assistant",
    page_icon="🧀",
    layout="wide"
)

st.title("🧀 Cheese Shopping Assistant")
st.write("Ask me anything about our cheese products!")

# Initialize agent
@st.cache_resource
def get_agent():
    return create_agent_graph()

agent = get_agent()

# Set up the UI
setup_ui(agent)

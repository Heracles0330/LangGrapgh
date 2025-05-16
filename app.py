import streamlit as st
from PIL import Image
import uuid
import os
import time # For simulating streaming if needed
import re # ADDED

# Attempt to import agent-specific modules
try:
    from agent.graph import create_agent_graph
    from langgraph.types import Command, Interrupt
    from langchain_core.messages import HumanMessage, AIMessage
except ImportError as e:
    st.error(f"Failed to import necessary agent modules: {e}. "
             "Please ensure your agent code is accessible and all dependencies are installed.")
    st.stop()

# --- Configuration ---
AGENT_NAME = "🧀 Cheese Shopping Assistant"
AGENT_DESCRIPTION = """
I am an AI assistant powered by LangGraph, here to help you with all your cheese-related queries!
I can search our product database, and if needed, browse the web for more general information.
Let me know what you're looking for!
"""
IMAGE_PATH = "agent_graph_mermaid_local.png" # Ensure this image exists in your project root

# --- Helper Functions ---
def initialize_session_state():
    """Initializes Streamlit session state variables."""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = [] # Stores full chat history (HumanMessage, AIMessage)
    if "agent_graph" not in st.session_state:
        try:
            st.session_state.agent_graph = create_agent_graph()
        except Exception as e:
            st.error(f"Failed to create agent graph: {e}")
            st.session_state.agent_graph = None
    if "current_thoughts" not in st.session_state:
        st.session_state.current_thoughts = []
    if "current_reason" not in st.session_state:
        st.session_state.current_reason = ""
    if "current_interrupt_message" not in st.session_state:
        st.session_state.current_interrupt_message = None
    if "current_interrupt_type" not in st.session_state:
        st.session_state.current_interrupt_type = None
    if "pending_user_action_for_interrupt" not in st.session_state:
        st.session_state.pending_user_action_for_interrupt = False

def reset_turn_specific_state():
    """Resets state variables that are specific to a single agent turn."""
    st.session_state.current_thoughts = []
    st.session_state.current_reason = ""
    # Don't reset interrupt message here, it's cleared after handling

def display_sidebar():
    """Displays the sidebar content."""
    with st.sidebar:
        st.title(AGENT_NAME)
        st.markdown(AGENT_DESCRIPTION)
        try:
            if os.path.exists(IMAGE_PATH):
                image = Image.open(IMAGE_PATH)
                st.image(image, caption="Agent Architecture", use_container_width=True)
            else:
                st.warning(f"Graph image not found at {IMAGE_PATH}")
        except Exception as e:
            st.error(f"Could not load graph image: {e}")
        
        if st.button("New Conversation"):
            # Clear the entire chat history
            st.session_state.messages = [] 
            # Generate a new thread_id for a completely fresh session state with the agent
            st.session_state.thread_id = str(uuid.uuid4())
            # Reset any turn-specific UI state
            reset_turn_specific_state()
            # Clear any pending interrupt information
            st.session_state.current_interrupt_message = None
            st.session_state.pending_user_action_for_interrupt = False
            st.session_state.current_interrupt_type = None
            # Clear thought and reason containers specifically if they were used
            # Note: reset_turn_specific_state already clears current_thoughts and current_reason data
            # No explicit need to empty containers here if st.rerun() rebuilds them empty.
            
            st.rerun()


def display_chat_messages():
    """Displays the chat history."""
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                render_markdown_with_interactive_images(msg["content"], f"chat_{i}")
        elif msg["role"] == "system":
             st.info(msg["content"])

# ADDED FUNCTION
def render_markdown_with_interactive_images(markdown_content, unique_key_prefix):
    """
    Renders markdown content. Text is passed to st.markdown.
    Images ![alt](url) are rendered as clickable thumbnails that open a dialog with the full image.
    """
    parts = re.split(r'(!\[.*?\]\(.*?\))', markdown_content) # Split by image tags, keeping them
    for i, part in enumerate(parts):
        if re.match(r'(!\[.*?\]\(.*?\))', part): # It's an image tag
            alt_match = re.search(r'!\[(.*?)\]', part)
            url_match = re.search(r'\((.*?)\)', part)
            alt_text = alt_match.group(1) if alt_match else "image"
            image_url = url_match.group(1) if url_match else None

            if image_url:
                # Display a smaller version or thumbnail
                st.image(image_url, caption=alt_text if alt_text else None, width=150)
                
                button_key = f"{unique_key_prefix}_zoom_button_{i}"
                if st.button("🔍 Zoom In", key=button_key):
                    # Use st.dialog to show the full image
                    # st.dialog requires Streamlit 1.33+
                    if hasattr(st, 'dialog'):
                        with st.dialog(f"Image: {alt_text}", expanded=True):
                            st.image(image_url, caption=alt_text if alt_text else None, use_column_width=True)
                    else:
                        # Fallback for older Streamlit versions (less ideal, just shows larger image inline)
                        st.warning("Zoom dialog requires Streamlit 1.33+. Displaying larger image inline.")
                        st.image(image_url, caption=alt_text if alt_text else None, use_column_width=True)
            else:
                st.markdown(part, unsafe_allow_html=True) # Render as markdown if URL not found
        else: # It's a text part
            if part.strip(): # Avoid rendering empty strings
                st.markdown(part, unsafe_allow_html=True)


# --- Main Application ---
initialize_session_state()
display_sidebar()

st.header("Chat with the Cheese Assistant")

display_chat_messages()

# Placeholders for streaming agent state
thought_container = st.empty()
reason_container = st.empty()
interrupt_display_container = st.empty()


def handle_interrupt_input():
    """Handles user input for an active interrupt."""
    if st.session_state.current_interrupt_type == "clarification":
        clarification_key = f"clarification_input_{st.session_state.thread_id}"
        user_clarification = st.chat_input("Please provide clarification:", key=clarification_key)
        if user_clarification:
            st.session_state.pending_user_action_for_interrupt = False # Action taken
            return Command(resume={"data": user_clarification})
            
    elif st.session_state.current_interrupt_type == "web_search":
        col1, col2 = st.columns(2)
        web_search_key_yes = f"web_search_yes_{st.session_state.thread_id}"
        web_search_key_no = f"web_search_no_{st.session_state.thread_id}"
        if col1.button("Yes, perform web search", key=web_search_key_yes):
            st.session_state.pending_user_action_for_interrupt = False # Action taken
            return Command(resume={"data": "yes"})
        if col2.button("No, do not search", key=web_search_key_no):
            st.session_state.pending_user_action_for_interrupt = False # Action taken
            return Command(resume={"data": "no"})
    return None


# Handle active interrupt input if any
resume_command = None
if st.session_state.pending_user_action_for_interrupt:
    with interrupt_display_container.container():
        st.warning(st.session_state.current_interrupt_message)
        resume_command = handle_interrupt_input()


# Handle new user query if no interrupt is pending user action
user_query = None
if not st.session_state.pending_user_action_for_interrupt:
    query_input_key = f"query_input_{st.session_state.thread_id}"
    user_query = st.chat_input("Ask something about cheese...", key=query_input_key)


# Core agent interaction logic
if resume_command or user_query:
    if st.session_state.agent_graph is None:
        st.error("Agent graph is not initialized. Cannot process query.")
        st.stop()

    if user_query: # New query
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.chat_message("user").markdown(user_query)
        reset_turn_specific_state() # Reset thoughts/reason for new query
        st.session_state.current_interrupt_message = None # Clear previous interrupt messages
        interrupt_display_container.empty()


        # Prepare initial state for the graph
        # This logic should align with how test_agent.py carries over messages
        # For a truly new thread_id, messages would typically start fresh or be explicitly loaded
        # If we're reusing thread_id logic from test_agent.py where messages are manually carried:
        
        # Simplified: for each new query in UI, if thread_id was reset by "New Conversation",
        # messages list in state is implicitly fresh.
        # If not, we need to fetch previous messages if we want to implement the
        # history-preserving new thread_id logic from previous discussions.
        # For now, let's assume the current `st.session_state.messages` provides the history.

        graph_messages_history = []
        for m in st.session_state.messages[:-1]: # Exclude current user query
            if m["role"] == "user":
                graph_messages_history.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                graph_messages_history.append(AIMessage(content=m["content"]))
        
        init_state = {
            "query": user_query,
            "messages": graph_messages_history, # Pass current history
            # Initialize other state fields as per your AgentState definition
            "needs_clarification": False,
            "reason": "",
            "suggested_clarifying_question": "",
            "plan": [],
            "thought": [],
            "is_database_searched": False,
            "searched_result": {},
            "pinecone_results": [],
            "mongo_results": [],
            "mongo_query": "",
            "pinecone_query": "",
            "is_result_sufficient": False,
            "needs_web_search": False,
            "web_search_query": "",
            "web_search_results": [],
            "final_response": ""
        }
        stream_input = init_state
    elif resume_command: # Resuming from interrupt
        # `resume_command` is already a Command object
        stream_input = resume_command
        st.session_state.current_interrupt_message = None # Clear displayed interrupt
        interrupt_display_container.empty()
        # Thoughts and reason from before interrupt might still be relevant or get overwritten.

    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    # --- Agent Streaming ---
    final_answer_placeholder = st.chat_message("assistant").empty()
    current_assistant_response_parts = []

    try:
        for event_part_index, event in enumerate(st.session_state.agent_graph.stream(stream_input, config=config, stream_mode="values")):
            # event is the full state dictionary at each step
            
            # Update Thoughts
            if "thought" in event and event["thought"]:
                # Assuming 'thought' is a list of strings
                new_thoughts = [t for t in event["thought"] if t not in st.session_state.current_thoughts]
                if new_thoughts:
                    st.session_state.current_thoughts.extend(new_thoughts)
                    thought_container.markdown("#### 🤔 Agent Thoughts:\n" + "\n".join([f"- {t}" for t in st.session_state.current_thoughts]))

            # Update Reason (from query_understanding)
            if "reason" in event and event["reason"] and event["reason"] != st.session_state.current_reason :
                # Only update if it's new information, specific to understanding node
                if "needs_clarification" in event: # characteristic of understanding node output
                     st.session_state.current_reason = event["reason"]
                     reason_container.markdown(f"**Understanding Reason:** {st.session_state.current_reason}")
            
            # Handle Interrupts
            if "__interrupt__" in event:
                interrupt_info = event["__interrupt__"][0] # Assuming one interrupt at a time
                st.session_state.current_interrupt_message = interrupt_info.value.get("message", "Agent needs input.")
                st.session_state.current_interrupt_type = interrupt_info.value.get("type", "unknown")
                st.session_state.pending_user_action_for_interrupt = True
                # Display the interrupt message and input fields by rerunning
                st.rerun() 
                # Break from stream processing as we await user input for interrupt

            # Handle Final Response (once available)
            if "final_response" in event and event["final_response"]:
                # The whole response comes at once when the node finishes.
                current_assistant_response_parts = [event["final_response"]] # Still useful for storing full response
                with final_answer_placeholder.container(): # Use container to render complex content
                    render_markdown_with_interactive_images(event["final_response"], f"stream_{event_part_index}")

            # If END is reached, store the final response.
            # The last event before END that has 'final_response' is what we want.
            # The condition above should capture it.

        # After stream completes (if not interrupted and reran)
        if current_assistant_response_parts:
             full_final_response = "".join(current_assistant_response_parts)
             st.session_state.messages.append({"role": "assistant", "content": full_final_response})
        
        # If the loop finished without setting pending_user_action_for_interrupt,
        # it means the turn is complete or ended without an interrupt.
        if not st.session_state.pending_user_action_for_interrupt:
            reset_turn_specific_state() # Clean up thoughts/reason for next turn
            thought_container.empty() # Clear the thought display
            reason_container.empty()  # Clear the reason display
            # No st.rerun() here if we just finished displaying the last part of a stream.
            # If we added to messages, Streamlit's natural flow will update.
            # However, if only placeholders were updated, a rerun might be needed if some state
            # should trigger it. For now, adding to messages should be enough for rerender.
            # If the last message was an AI response, it gets added.
            if user_query or resume_command: # If an action was processed
                 st.rerun() # Rerun to reflect the new message in history and clear inputs


    except Exception as e:
        st.error(f"Error during agent execution: {e}")
        # Clean up temporary displays on error
        reset_turn_specific_state()
        thought_container.empty()
        reason_container.empty()

elif not st.session_state.messages: # Initial state of the app
    st.info("Ask me something about our cheese products to get started!")

import streamlit as st
from PIL import Image
import uuid
import os
import time # For simulating streaming if needed
import re

# Set page config as the first Streamlit command
st.set_page_config(layout="wide")

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
    """Resets state variables that are specific to a single agent turn's data."""
    # These hold the data, the containers display it.
    st.session_state.current_thoughts = []
    st.session_state.current_reason = ""
    # Don't reset interrupt message here, it's cleared after handling or on new query

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
            st.session_state.messages = [] 
            st.session_state.thread_id = str(uuid.uuid4())
            reset_turn_specific_state() # Clear data
            # Clear visual containers for thoughts/reasons for the new conversation
            thought_container.empty() 
            reason_container.empty()
            interrupt_display_container.empty() # Also clear any lingering interrupt display
            st.session_state.current_interrupt_message = None
            st.session_state.pending_user_action_for_interrupt = False
            st.session_state.current_interrupt_type = None
            st.rerun()


def display_chat_messages():
    """Displays the chat history."""
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        elif msg["role"] == "assistant":
            # If it's a system notice, render it slightly differently or just as markdown
            if msg["content"].startswith("**System Notice"):
                st.chat_message("assistant").warning(msg["content"]) # Or .info()
            else:
                with st.chat_message("assistant"):
                    render_markdown_with_interactive_images(msg["content"], f"chat_{i}")
        elif msg["role"] == "system": # For "--- New Conversation Started ---" type messages
             st.info(msg["content"])

def render_markdown_with_interactive_images(markdown_content, unique_key_prefix):
    """Renders markdown content. Text is passed to st.markdown. Images are rendered directly."""
    parts = re.split(r'(!\[.*?\]\(.*?\))', markdown_content) 
    for i, part in enumerate(parts):
        if re.match(r'(!\[.*?\]\(.*?\))', part): 
            alt_match = re.search(r'!\[(.*?)\]', part)
            url_match = re.search(r'\((.*?)\)', part)
            alt_text = alt_match.group(1) if alt_match else "image"
            image_url = url_match.group(1) if url_match else None

            if image_url:
                st.image(image_url, caption=alt_text if alt_text else None, use_container_width='auto')
            else:
                st.markdown(part, unsafe_allow_html=True) 
        else: 
            if part.strip(): 
                st.markdown(part, unsafe_allow_html=True)


# --- Main Application ---
initialize_session_state()

# Define placeholders at the top level so they persist across reruns
# These will be populated during agent streaming for the current turn.
thought_container = st.empty()
reason_container = st.empty()
interrupt_display_container = st.empty()

display_sidebar() # Sidebar can now also clear these containers via New Conversation button

st.header("Chat with the Cheese Assistant")
display_chat_messages()


def handle_interrupt_input():
    """Handles user input for an active interrupt."""
    if st.session_state.current_interrupt_type == "clarification":
        clarification_key = f"clarification_input_{st.session_state.thread_id}"
        user_clarification = st.chat_input("Please provide clarification:", key=clarification_key)
        if user_clarification:
            st.session_state.messages.append({"role": "user", "content": f"(Clarification provided) {user_clarification}"})
            st.session_state.pending_user_action_for_interrupt = False 
            # Clear the specific interrupt prompt from display now that it's handled
            interrupt_display_container.empty() 
            return Command(resume={"data": user_clarification})
            
    elif st.session_state.current_interrupt_type == "web_search":
        # For buttons, display them within the interrupt_display_container
        with interrupt_display_container.container():
            st.warning(st.session_state.current_interrupt_message) # Re-display message with buttons
            col1, col2 = st.columns(2)
            web_search_key_yes = f"web_search_yes_{st.session_state.thread_id}"
            web_search_key_no = f"web_search_no_{st.session_state.thread_id}"
            if col1.button("Yes, perform web search", key=web_search_key_yes):
                st.session_state.messages.append({"role": "user", "content": "(User action: Yes, perform web search)"})
                st.session_state.pending_user_action_for_interrupt = False 
                interrupt_display_container.empty() 
                return Command(resume={"data": "yes"})
            if col2.button("No, do not search", key=web_search_key_no):
                st.session_state.messages.append({"role": "user", "content": "(User action: No, do not search)"})
                st.session_state.pending_user_action_for_interrupt = False 
                interrupt_display_container.empty() 
                return Command(resume={"data": "no"})
    return None

resume_command = None
if st.session_state.pending_user_action_for_interrupt and not st.session_state.current_interrupt_type == "web_search":
    # Only display generic warning if it's not web_search, as web_search handles its own display with buttons
    with interrupt_display_container.container():
        st.warning(st.session_state.current_interrupt_message)

if st.session_state.pending_user_action_for_interrupt: # Call handle_interrupt_input if pending
    resume_command = handle_interrupt_input()


user_query = None
if not st.session_state.pending_user_action_for_interrupt: # Only allow new query if no interrupt is active
    query_input_key = f"query_input_{st.session_state.thread_id}"
    user_query = st.chat_input("Ask something about cheese...", key=query_input_key)


# Core agent interaction logic
if resume_command or user_query:
    try:
        if st.session_state.agent_graph is None:
            st.error("Agent graph is not initialized. Cannot process query.")
            st.stop()

        stream_input = None 
        if user_query: 
            st.session_state.messages.append({"role": "user", "content": user_query})
            # Display the user query immediately
            with st.chat_message("user"):
                st.markdown(user_query)
            
            reset_turn_specific_state() # Clear previous turn's thought/reason data
            # Clear visual containers for the new turn's thoughts/reasons
            thought_container.empty() 
            reason_container.empty()
            # No need to clear interrupt_display_container here, it's for ongoing interrupts
            
            st.session_state.current_interrupt_message = None # Clear any previous interrupt data
            st.session_state.pending_user_action_for_interrupt = False

            graph_messages_history = []
            # Prepare history, excluding the very last user message which is the current query
            for m in st.session_state.messages[:-1]: 
                if m["role"] == "user":
                    graph_messages_history.append(HumanMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    graph_messages_history.append(AIMessage(content=m["content"]))
            
            init_state = {
                "query": user_query, 
                "messages": graph_messages_history,
                "needs_clarification": False, "reason": "", "suggested_clarifying_question": "",
                "plan": [], "thought": [], "is_database_searched": False,
                "searched_result": {}, "pinecone_results": [], "mongo_results": [],
                "mongo_query": "", "pinecone_query": "", "is_result_sufficient": False,
                "needs_web_search": False, "web_search_query": "", "web_search_results": [],
                "final_response": ""
            }
            stream_input = init_state
        elif resume_command: 
            stream_input = resume_command
            # Thoughts/reason from before interrupt will be displayed as they were.
            # If new thoughts/reasons are generated after resume, they will append.
            # No need to clear thought/reason containers on resume.
            # interrupt_display_container is cleared when interrupt is handled.

        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        
        final_answer_placeholder = st.chat_message("assistant").empty()
        
        if stream_input is not None: 
            # --- Agent Streaming ---
            # accumulated_final_response_for_turn is used to build the response before adding to history
            accumulated_final_response_for_turn = ""
            
            with st.spinner("🧀 Cheese Assistant is thinking..."):
                for event_part_index, event in enumerate(st.session_state.agent_graph.stream(stream_input, config=config, stream_mode="values")):
                    if "thought" in event and event["thought"]:
                        new_thoughts = [t for t in event["thought"] if t not in st.session_state.current_thoughts]
                        if new_thoughts:
                            st.session_state.current_thoughts.extend(new_thoughts)
                            with thought_container.container(): 
                                 with st.expander("🤔 Agent Thoughts", expanded=True):
                                    for t_content in st.session_state.current_thoughts: 
                                        st.markdown(f"- {t_content}", help="Internal thought process of the agent.")

                    if "reason" in event and event["reason"] and event["reason"] != st.session_state.current_reason:
                        if "needs_clarification" in event: 
                             st.session_state.current_reason = event["reason"]
                             with reason_container.container(): 
                                with st.expander("💡 Understanding Reason", expanded=True):
                                    st.markdown(st.session_state.current_reason, help="Agent\'s reason from the understanding phase.")
                    
                    if "__interrupt__" in event:
                        interrupt_info = event["__interrupt__"][0]
                        st.session_state.current_interrupt_message = interrupt_info.value.get("message", "Agent needs input.")
                        st.session_state.current_interrupt_type = interrupt_info.value.get("type", "unknown")
                        st.session_state.pending_user_action_for_interrupt = True
                        
                        # Add interrupt message to chat history for display & update UI
                        # Make sure it has a unique content to avoid issues if same interrupt happens twice
                        interrupt_chat_content = f"**System Notice (requires your input):**\n{st.session_state.current_interrupt_message} (Ref: {uuid.uuid4().hex[:6]})"
                        if not st.session_state.messages or st.session_state.messages[-1]["content"] != interrupt_chat_content:
                            st.session_state.messages.append({"role": "assistant", "content": interrupt_chat_content})
                        
                        # Clear spinner before rerunning for interrupt
                        # The spinner is outside the loop, clearing it via placeholder is not direct here.
                        # Instead, the rerun will handle it. The spinner will only show if `is_agent_thinking` is true.
                        # For now, let the rerun handle the spinner clearing by re-evaluating the page. 
                        st.rerun() 
                        break # Exit stream processing for this turn

                    if "final_response" in event and event["final_response"]:
                        accumulated_final_response_for_turn = event["final_response"]
                        with final_answer_placeholder.container():
                            render_markdown_with_interactive_images(accumulated_final_response_for_turn, f"final_stream_{event_part_index}")
                        # Break after getting the final response if it's not chunked/streamed character by character
                        # If your agent DOES stream final_response in chunks, this logic needs adjustment
                        # For now, assume final_response is a complete message. Then break.
                        break 

            # After the streaming loop finishes or breaks (e.g. for final_response)
            if accumulated_final_response_for_turn:
                # Add to message history only if it's new
                if not st.session_state.messages or st.session_state.messages[-1]["content"] != accumulated_final_response_for_turn:
                    st.session_state.messages.append({"role": "assistant", "content": accumulated_final_response_for_turn})
            
            # If an interrupt was not handled (e.g. if break happened for final_response before interrupt section)
            # and an interrupt IS pending, rerun to show interrupt UI.
            if st.session_state.pending_user_action_for_interrupt:
                st.rerun()
            else: # Normal completion of a turn (final answer processed, no pending interrupt)
                # The thoughts and reasons for THIS turn remain displayed.
                # reset_turn_specific_state() was called at the START of new user query processing.
                # We don't call it here to let the thoughts/reasons persist.
                # Rerun to ensure UI is updated with the final message and state.
                st.rerun() 

    except Exception as e:
        st.error(f"Error during agent execution: {e}")
        reset_turn_specific_state() # Clear data
        thought_container.empty()   # Clear display
        reason_container.empty()    # Clear display
        interrupt_display_container.empty()

elif not st.session_state.messages: 
    st.info("Ask me something about our cheese products to get started!")

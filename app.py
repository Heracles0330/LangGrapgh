import streamlit as st
import uuid
from pathlib import Path

# --- Page Configuration (Must be the first Streamlit command) ---
st.set_page_config(page_title="Cheese Chatbot", layout="wide")

# --- Agent and LangGraph Setup ---
from agent.graph import agent_graph # Use your actual agent graph
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage # Import message types
from langgraph.types import Command, Interrupt # Ensure Interrupt is available if needed for type checking, though not directly sent by UI
from dotenv import load_dotenv

load_dotenv() # Load environment variables if you have a .env file

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = [] # For UI display: List[Dict{"role": str, "content": str, ...}]
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "interrupted_state" not in st.session_state:
    st.session_state.interrupted_state = False
if "current_config" not in st.session_state:
    st.session_state.current_config = {"configurable": {"thread_id": st.session_state.thread_id}}
if "last_config_for_carry_over" not in st.session_state:
    st.session_state.last_config_for_carry_over = None
# For actual agent state carry-over
if "carried_over_messages_from_graph" not in st.session_state:
    st.session_state.carried_over_messages_from_graph = [] # List[BaseMessage]
if "current_thoughts_displayed" not in st.session_state:
    st.session_state.current_thoughts_displayed = set()
if "last_event_messages_count" not in st.session_state:
    st.session_state.last_event_messages_count = 0
if "active_interrupt_info" not in st.session_state: # To store details of an active interrupt
    st.session_state.active_interrupt_info = None
if "last_displayed_plan" not in st.session_state: # To track the last displayed plan
    st.session_state.last_displayed_plan = []


# --- Sidebar ---
with st.sidebar:
    st.title("🧀 Cheese Chatbot")
    st.caption("Your AI assistant for all things cheese!")
    
    try:
        image_path = Path("agent_graph_mermaid_local.png") # Use the correct image name
        if image_path.is_file():
            st.image(str(image_path), caption="Agent Logic Flow", use_container_width=True)
        else:
            st.write("_(Agent graph image 'agent_graph_mermaid_local.png' not found)_\n")
    except Exception as e:
        st.error(f"Error loading image: {e}")

    st.markdown("---")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.interrupted_state = False
        st.session_state.thread_id = str(uuid.uuid4()) 
        st.session_state.current_config = {"configurable": {"thread_id": st.session_state.thread_id}}
        st.session_state.last_config_for_carry_over = None
        st.session_state.carried_over_messages_from_graph = []
        st.session_state.current_thoughts_displayed = set()
        st.session_state.last_event_messages_count = 0
        st.session_state.active_interrupt_info = None
        st.session_state.last_displayed_plan = [] # Reset on clear
        st.rerun()

# --- Main Chat Interface ---
st.header("Chat with the Cheese Connoisseur")

# Display chat messages
for msg_idx, ui_message in enumerate(st.session_state.messages):
    role = ui_message.get("role", "assistant") 
    content = ui_message.get("content", "")
    
    with st.chat_message(role):
        if role == "reasoning_thought":
            st.markdown(f"🤔 *Thinking: {content}*")
        elif role == "reasoning_interrupt":
            st.markdown(f"⚠️ **Agent Action Required:** {content}")
            if "reason" in ui_message:
                 st.info(f"Reason: {ui_message['reason']}")
            if "web_search_query" in ui_message:
                 query_text = ui_message['web_search_query']
                 st.warning(f"The agent proposes to search the web for: **{query_text}**")
                 
                 col1, col2, _ = st.columns([1,1,3]) # Create columns for buttons
                 with col1:
                    yes_key = f"web_search_yes_{msg_idx}"
                    if st.button(f"✅ Yes, search", key=yes_key, help=f"Confirm search for: {query_text}"):
                        st.session_state.user_input_for_agent = "yes"
                        # No st.rerun() here, it's handled after the main input prompt logic
                 with col2:
                    no_key = f"web_search_no_{msg_idx}"
                    if st.button(f"❌ No, skip", key=no_key, help="Decline web search"):
                        st.session_state.user_input_for_agent = "no"
                        # No st.rerun() here
                 
                 # If a button was clicked, user_input_for_agent is set.
                 # The existing main st.rerun() at the end of the script will handle it.
                 # We need to ensure the input field is not processed if a button is clicked
                 # This is implicitly handled because if prompt is set by button, chat_input won't be.

            # The generic input box will handle the user's response to other interrupts or text input
        else: # user, assistant
            st.markdown(content)


# Handle user input and agent interaction
user_responded_to_button = False
if "user_input_for_agent" in st.session_state and st.session_state.user_input_for_agent: # For button clicks
    prompt = st.session_state.user_input_for_agent
    st.session_state.user_input_for_agent = None 
    user_responded_to_button = True # Mark that input came from a button
else:
    # Only show chat_input if not currently handling a button response AND agent is not interrupted waiting for specific button
    # Or, more simply, always show chat_input but prioritize button input.
    # The `user_responded_to_button` flag helps to avoid processing chat_input if a button was just clicked.
    prompt = st.chat_input("Ask about cheese or respond to the agent...")

if prompt: # This will be true if chat_input has value OR if a button set the prompt
    if not user_responded_to_button: # If input is from chat_input, display it as user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): 
            st.markdown(prompt)
    # Else (if user_responded_to_button), 'prompt' is "yes" or "no". 
    # We still want to send this to the agent, but we've already handled the user message part
    # by not re-displaying "yes" or "no" as a separate user chat bubble.
    # The "Resuming with input..." thought will indicate what's being sent.

    st.session_state.current_thoughts_displayed = set() 
    st.session_state.last_event_messages_count = 0 
    # Don't reset last_displayed_plan here, only if it changes in the stream or on full clear.

    with st.spinner("Cheese bot is thinking..."):
        try:
            events_iterable = None
            if st.session_state.interrupted_state:
                actual_command = Command(resume={"data": prompt}) 
                
                st.session_state.messages.append({
                    "role": "reasoning_thought", 
                    "content": f"Resuming with input: '{prompt}'"
                })
                
                events_iterable = agent_graph.stream(
                    actual_command,
                    config=st.session_state.current_config,
                    stream_mode="values"
                )
                st.session_state.interrupted_state = False 
                st.session_state.active_interrupt_info = None

            else: # New conversation flow
                st.session_state.last_config_for_carry_over = st.session_state.current_config.copy()
                
                new_thread_id = str(uuid.uuid4())
                st.session_state.thread_id = new_thread_id
                st.session_state.current_config = {"configurable": {"thread_id": new_thread_id}}
                
                # --- Message Carry-Over ---
                st.session_state.carried_over_messages_from_graph = [] # Reset
                if st.session_state.last_config_for_carry_over:
                    try:
                        previous_state_snapshot = agent_graph.get_state(st.session_state.last_config_for_carry_over)
                        if previous_state_snapshot and previous_state_snapshot.values:
                            retrieved_messages = previous_state_snapshot.values.get("messages", [])
                            if retrieved_messages: # retrieved_messages are List[BaseMessage]
                                st.session_state.carried_over_messages_from_graph = [m for m in retrieved_messages if isinstance(m, BaseMessage)]
                                st.session_state.messages.append({
                                    "role": "reasoning_thought", 
                                    "content": f"Carried over {len(st.session_state.carried_over_messages_from_graph)} messages from previous interaction (Thread ID: ...{st.session_state.last_config_for_carry_over.get('configurable',{}).get('thread_id', '')[-6:]})."
                                })
                    except Exception as e:
                        st.warning(f"Info: Could not retrieve state from previous session ({st.session_state.last_config_for_carry_over.get('configurable',{}).get('thread_id', '')[-6:]}): {e}. Starting fresh.")
                        st.session_state.carried_over_messages_from_graph = []
                
                init_state = {
                    "query": prompt, # Current user query
                    "messages": st.session_state.carried_over_messages_from_graph, # List[BaseMessage]
                    "needs_clarification": False, # Defaults for a new run
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
                    "web_search_query": ""
                }
                events_iterable = agent_graph.stream(
                    init_state,
                    config=st.session_state.current_config,
                    stream_mode="values"
                )

            # --- Process events from the stream ---
            if events_iterable:
                for event_idx, event_state in enumerate(events_iterable): # event_state is AgentState
                    # --- Handle Interrupts ---
                    if "__interrupt__" in event_state:
                        interrupt_obj = event_state["__interrupt__"][0] # This is an Interrupt object
                        interrupt_value = interrupt_obj.value # This is the dictionary payload

                        interrupt_message_content = interrupt_value.get("message", "Interruption: Agent requires input.")
                        clarification_reason = interrupt_value.get("reason")
                        suggested_question = interrupt_value.get("suggested_clarifying_question")
                        web_search_query = interrupt_value.get("web_search_query")
                        
                        st.session_state.active_interrupt_info = interrupt_value # Store for context

                        ui_interrupt_msg = {"role": "reasoning_interrupt", "content": interrupt_message_content}
                        
                        if suggested_question: # Prefer suggested_question if available for clarification
                             ui_interrupt_msg["reason"] = suggested_question
                        elif clarification_reason:
                             ui_interrupt_msg["reason"] = clarification_reason
                        
                        if web_search_query:
                            ui_interrupt_msg["web_search_query"] = web_search_query
                        
                        st.session_state.messages.append(ui_interrupt_msg)
                        st.session_state.interrupted_state = True
                        break # Stop processing further events on interrupt

                    # --- Display Agent Thoughts (List[str]) ---
                    agent_thoughts = event_state.get("thought", []) 
                    if agent_thoughts:
                        # Display only the latest new thought to avoid clutter if thoughts are cumulative
                        latest_thought = agent_thoughts[-1] if agent_thoughts else None
                        if latest_thought and latest_thought not in st.session_state.current_thoughts_displayed:
                            st.session_state.messages.append({"role": "reasoning_thought", "content": latest_thought})
                            st.session_state.current_thoughts_displayed.add(latest_thought)

                    # --- Display Agent Plan (List[str]) ---
                    agent_plan = event_state.get("plan", [])
                    if agent_plan and st.session_state.get("last_displayed_plan") != agent_plan:
                       plan_text = "📝 **Devising a plan:**\n" + "\n".join([f"  - {step}" for step in agent_plan])
                       st.session_state.messages.append({"role": "reasoning_thought", "content": plan_text})
                       st.session_state.last_displayed_plan = agent_plan


                    # --- Display New AIMessages ---
                    # event_state["messages"] contains List[BaseMessage]
                    current_graph_messages = event_state.get("messages", [])
                    new_messages_from_event = current_graph_messages[st.session_state.last_event_messages_count:]
                    
                    for msg_from_graph in new_messages_from_event:
                        if isinstance(msg_from_graph, AIMessage):
                            st.session_state.messages.append({"role": "assistant", "content": msg_from_graph.content})
                        # HumanMessages are added when user types, SystemMessages could be handled if needed
                    st.session_state.last_event_messages_count = len(current_graph_messages)

                    # --- Display Clarification Info (if not leading to an immediate interrupt shown above) ---
                    # This might be redundant if all clarifications cause an interrupt that's already handled.
                    if event_state.get("needs_clarification") and not st.session_state.interrupted_state:
                        reason = event_state.get("reason","")
                        question = event_state.get("suggested_clarifying_question","")
                        # Avoid displaying if it's already part of an active interrupt message
                        if not (st.session_state.active_interrupt_info and \
                           (st.session_state.active_interrupt_info.get("reason") == reason or \
                            st.session_state.active_interrupt_info.get("suggested_clarifying_question") == question)):
                            
                            if reason or question:
                                clar_text_parts = ["The agent requires clarification."]
                                if reason: clar_text_parts.append(f"Reason: {reason}")
                                if question: clar_text_parts.append(f"Question: {question}")
                                # Display as a thought or a distinct system message
                                st.session_state.messages.append({"role": "reasoning_thought", "content": " ".join(clar_text_parts)})
                    
                    # Final response check from state (if your agent populates this field)
                    final_response_from_state = event_state.get("final_response")
                    if final_response_from_state and isinstance(final_response_from_state, str):
                        # Ensure this isn't a duplicate of the last AIMessage
                        if not st.session_state.messages or st.session_state.messages[-1].get("content") != final_response_from_state or st.session_state.messages[-1].get("role") != "assistant":
                            st.session_state.messages.append({"role": "assistant", "content": final_response_from_state})


        except Exception as e:
            st.error(f"An error occurred while interacting with the agent: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"Sorry, an error occurred: {str(e)}"})
            # Potentially reset interrupt state if error is critical
            # st.session_state.interrupted_state = False 

    st.rerun() # Rerun to display new messages and update UI state

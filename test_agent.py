from agent.graph import agent_graph
from langchain_core.messages import HumanMessage
from langgraph.types import Command, Interrupt
from dotenv import load_dotenv
import uuid
config = {"configurable": {"thread_id": "initial_thread"}}

load_dotenv()
interrupted_state = False

while True:
    try:
        # print(interrupted_state)
        user_input = input("Enter a message: ")
        
        if interrupted_state:
            events = agent_graph.stream(
                Command(resume={"data":user_input}),
                config=config, 
                stream_mode="values",
            )
            interrupted_state = False
        else:
            config_of_previous_session = config.copy()

            new_thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": new_thread_id}}

            messages_to_carry_over = []
            try:
                previous_state_snapshot = agent_graph.get_state(config_of_previous_session)
                if previous_state_snapshot and previous_state_snapshot.values:
                    messages_to_carry_over = previous_state_snapshot.values.get("messages", [])
            except Exception as e:
                print(f"Info: Could not retrieve state from previous session ({config_of_previous_session.get('configurable', {}).get('thread_id')}): {e}. Starting with fresh history.")
                messages_to_carry_over = []

            init_state = {
                "query": user_input,
                "messages": messages_to_carry_over,
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
                "web_search_query": ""
            }
            events = agent_graph.stream(
                init_state, 
                config=config,
                stream_mode="values",
            )
        
        for event in events:
            if '__interrupt__' in event:
                message = event['__interrupt__'][0].value['message']
                print(message)
                interrupted_state = True
                break
    except Exception as e:
        print(f"Error occurred: {e}")
        resume = input("Do you want to continue? (y/n): ")
        if resume.lower() != 'y':
            break
        
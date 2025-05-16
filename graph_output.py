from IPython.display import Image, display
from agent.graph import agent_graph

display(Image(agent_graph.get_graph().draw_mermaid_png()))
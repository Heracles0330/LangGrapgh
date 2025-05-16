# save_graph_image.py
from agent.graph import create_agent_graph 
# ADD this import for MermaidDrawMethod
from langgraph.graph.state import MermaidDrawMethod

def save_graph_as_png():
    print("Creating and compiling the agent graph...")
    try:
        agent_graph = create_agent_graph()
        print("Graph compiled.")
    except Exception as e:
        print(f"Error creating graph: {e}")
        return

    # Attempt to use draw_mermaid_png with Pyppeteer
    try:
        print("Attempting to generate PNG using draw_mermaid_png() with Pyppeteer (local rendering)...")
        # This method requires Pyppeteer.
        # If not installed, run: pip install pyppeteer
        # Pyppeteer will download Chromium on its first run.
        png_bytes = agent_graph.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.PYPPETEER
        )
        output_file_path = "agent_graph_mermaid_local.png"
        with open(output_file_path, "wb") as f:
            f.write(png_bytes)
        print(f"Graph successfully saved to {output_file_path}")
        return # Success
    except ImportError as ie:
        print(f"ImportError with draw_mermaid_png (Pyppeteer): {ie}")
        print("This likely means 'pyppeteer' is missing.")
        print("Please install it with: pip install pyppeteer")
    except RuntimeError as re: # Pyppeteer can raise RuntimeError if Chromium download fails
        print(f"RuntimeError with Pyppeteer: {re}")
        print("This might be due to an issue downloading or finding Chromium.")
        print("Ensure your EC2 instance has internet access for the initial Chromium download by Pyppeteer.")
    except AttributeError:
        print("draw_mermaid_png() method not found on agent_graph.get_graph() or MermaidDrawMethod not available.")
    except Exception as e_mermaid_local:
        print(f"Error using draw_mermaid_png with Pyppeteer: {e_mermaid_local}")

    # Fallback or alternative: try using draw_png (requires pygraphviz)
    # This part remains the same if you want to keep it as a fallback
    print("\nAttempting to generate PNG using draw_png() as an alternative (requires pygraphviz)...")
    try:
        png_bytes_gv = agent_graph.get_graph().draw_png()
        output_file_path_gv = "agent_graph_pygraphviz.png"
        with open(output_file_path_gv, "wb") as f:
            f.write(png_bytes_gv)
        print(f"Graph successfully saved to {output_file_path_gv}")
    except ImportError:
        print("ImportError with draw_png: 'pygraphviz' is likely not installed.")
        print("Please install it: pip install pygraphviz")
        print("Also ensure the Graphviz system library is installed.")
    except AttributeError:
        print("draw_png() method not found on agent_graph.get_graph().")
    except Exception as e_gv:
        print(f"Error using draw_png: {e_gv}")
        print("Ensure Graphviz is correctly installed and in your system's PATH if using pygraphviz.")

if __name__ == "__main__":
    save_graph_as_png()
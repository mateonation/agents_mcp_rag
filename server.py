from mcp.server.fastmcp import FastMCP
import chromadb
import os

# Init MCP server
mcp = FastMCP("TDAH_Coach")

# Connect to DB (RAG)
path_db = "./chroma_db"
client = chromadb.PersistentClient(path=path_db)
collection = client.get_collection(name="tdah_resources")

@mcp.tool()
def search_focus_strategy(query: str) -> str:
    """
    Search TDAH strategies in the knowledge base (RAG Tool).
    """
    res = collection.query(query_texts=[query], n_results=3)
    
    if not res['documents'] or not res['documents'][0]:
        return "No relevant strategies found."
        
    # Return chunks joined by separator
    return "\n---\n".join(res['documents'][0])

@mcp.tool()
def add_tada_list_item(achievement: str) -> str:
    """
    Save a micro-achievement to the Ta-Da list file (Related Tool).
    """
    file_path = "tada_list.txt"
    
    # Append achievement to file
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"- {achievement}\n")
        
    return f"Achievement '{achievement}' saved to Ta-Da list!"

@mcp.tool()
def get_weather_impact(location: str) -> str:
    """
    Get weather to anticipate mood/energy changes (Unrelated Tool).
    """
    return f"Weather in {location}: Cloudy, 18°C. Good weather to stay indoors."

if __name__ == "__main__":
    # Run server
    mcp.run()
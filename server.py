from mcp.server.fastmcp import FastMCP
import chromadb
import requests

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
        
    return "\n---\n".join(res['documents'][0])

@mcp.tool()
def add_tada_list_item(achievement: str) -> str:
    """
    Save a micro-achievement to the Ta-Da list file (Related Tool).
    """
    file_path = "tada_list.txt"
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"- {achievement}\n")
    return f"Achievement '{achievement}' saved to Ta-Da list!"

@mcp.tool()
def get_weather_impact(location: str) -> str:
    """
    Get real-time weather from internet to anticipate mood (Unrelated Tool).
    """
    try:
        # Replace spaces with '+' for the URL
        safe_city = location.replace(" ", "+")
        url = f"https://wttr.in/{safe_city}?format=%C,+%t"
        
        # VERY IMPORTANT: Disguise the request so the website doesn't block Python
        headers = {'User-Agent': 'curl/7.68.0'}
        
        # Increased timeout to 10 seconds just in case the internet is slow
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            weather_data = response.text.strip()
            return f"The current real weather in {location} is: {weather_data}."
        else:
            return f"Could not fetch weather for {location}. Status: {response.status_code}"
            
    except Exception as e:
        return f"Error connecting to internet: {str(e)}"

if __name__ == "__main__":
    mcp.run()
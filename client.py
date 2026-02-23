import asyncio
import json
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Init local LLM via Ollama
llm = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama" 
)

SYSTEM_PROMPT = """
Eres un Coach de Productividad especializado en TDAH. Tu tono debe ser paciente, motivador y claro. 
Tienes acceso a herramientas externas y debes cumplir estas reglas A RAJA TABLA:
1. Cuando el usuario te pida un consejo o ayuda para enfocarse, es OBLIGATORIO que primero uses la herramienta 'search_focus_strategy' para consultar la base de conocimientos. No inventes estrategias.
2. Cuando el usuario te cuente que ha logrado hacer una tarea, es OBLIGATORIO que uses la herramienta 'add_tada_list_item' para guardarlo.
3. Usa 'get_weather_impact' solo si el usuario menciona el clima.
"""

# Ultimate shield against invisible/surrogate characters
def sanitize_text(text) -> str:
    if not text:
        return ""
    # Strip characters in the surrogate range that crash the JSON encoder
    return "".join(c for c in str(text) if not (0xD800 <= ord(c) <= 0xDFFF))

async def run_agent():
    server_params = StdioServerParameters(command="python", args=["server.py"])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            mcp_tools = await session.list_tools()
            print("[+] Connected to MCP. Tools loaded.")
            
            local_tools = []
            for t in mcp_tools.tools:
                local_tools.append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema
                    }
                })

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("\n=== Local ADHD Coach Ready ===")
            print("Type 'exit' to quit.\n")

            while True:
                user_msg = sanitize_text(input("You: "))
                if user_msg.lower() == 'exit':
                    break
                    
                messages.append({"role": "user", "content": user_msg})

                response = await llm.chat.completions.create(
                    model="llama3.2",
                    messages=messages,
                    tools=local_tools
                )
                
                msg = response.choices[0].message
                
                if msg.tool_calls:
                    safe_tool_calls = []
                    for tc in msg.tool_calls:
                        safe_tool_calls.append({
                            "id": sanitize_text(tc.id),
                            "type": "function",
                            "function": {
                                "name": sanitize_text(tc.function.name),
                                "arguments": sanitize_text(tc.function.arguments)
                            }
                        })
                        
                    messages.append({
                        "role": "assistant",
                        "content": sanitize_text(msg.content) if msg.content else None,
                        "tool_calls": safe_tool_calls
                    })

                    for tool_call in msg.tool_calls:
                        print(f"\n[*] Using tool: {sanitize_text(tool_call.function.name)}...")
                        safe_args_str = sanitize_text(tool_call.function.arguments)
                        
                        try:
                            args = json.loads(safe_args_str)
                        except json.JSONDecodeError:
                            args = {}
                            
                        result = await session.call_tool(tool_call.function.name, args)
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": sanitize_text(tool_call.id),
                            "content": sanitize_text(str(result.content))
                        })
                        
                    final_response = await llm.chat.completions.create(
                        model="llama3.2",
                        messages=messages
                    )
                    final_msg = sanitize_text(final_response.choices[0].message.content)
                    messages.append({"role": "assistant", "content": final_msg})
                    print(f"\nCoach: {final_msg}\n")
                    
                else:
                    safe_reply = sanitize_text(msg.content)
                    messages.append({"role": "assistant", "content": safe_reply})
                    print(f"\nCoach: {safe_reply}\n")

if __name__ == "__main__":
    asyncio.run(run_agent())
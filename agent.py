import asyncio
import os
from langchain_mcp_adapters.client import MultiServerMCPClient

# 1. We brought back your favorite LLM provider!
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
# here is the chat
# Paste your actual working Groq API key here!
os.environ["GROQ_API_KEY"] = ""

async def run_unreal_agent():
    print("🤖 Booting up Llama 3 via Groq and connecting to Unreal Engine...")
    
    # Connect to your Unreal tools
    client = MultiServerMCPClient({
        "UnrealToy": {
            "command": "python",
            "args": ["C:\\Desktop\\Unreal-MCP\\server.py"],
            "transport": "stdio"
        }
    })
        
    tools = await client.get_tools()
    print(f"🛠️  Loaded {len(tools)} tools from FastMCP.")
    
    # 2. Initialize Groq (using a fast tool-calling model)
    llm = ChatGroq(
        model="llama-3.1-8b-instant", 
        temperature=0
    )
    
    # Create the Agent
    agent = create_agent(llm, tools)
    
    prompt = "Spawn a pointlight at X:0, Y:0, Z:100. Next, use the list_actors tool to find the exact name of the light you just spawned. Finally, use that name to change its color to pure Red. Then list all the actors to confirm it worked."
    print(f"\n🗣️ Prompt: {prompt}\n")
    
    # Execute the agent
    response = await agent.ainvoke({
        "messages": [HumanMessage(content=prompt)]
    })
    
    # Print the final answer
    print("\n✅ Final Response:")
    print(response["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(run_unreal_agent())
import asyncio
import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_xai import ChatXAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

# Make sure you set your Grok API key!
os.environ["XAI_API_KEY"] = ""

async def run_unreal_agent():
    print("🤖 Booting up Grok and connecting to Unreal Engine...")
    
    # 1. Initialize the client WITHOUT 'async with'
    client = MultiServerMCPClient({
        "UnrealToy": {
            "command": "python",
            "args": ["C:\\Desktop\\Unreal-MCP\\server.py"],
            "transport": "stdio" # Explicitly define the transport method
        }
    })
        
    # 2. Grab the tools (spawn_actor, list_actors) from server.py
    tools = await client.get_tools()
    print(f"🛠️  Loaded {len(tools)} tools from FastMCP.")
    
    # 3. Initialize Grok
    # Pass the key directly as an argument, bypassing the OS environment
    llm = ChatXAI(
        model="", 
        temperature=0,
        xai_api_key="" 
    )
    
    # 4. Create the LangChain/LangGraph Agent
    agent = create_agent(llm, tools)
    
    # 5. Tell Grok what to do!
    prompt = "Use your tools to spawn a pointlight in the Unreal Engine level at coordinates X:0, Y:0, Z:200. Then list all the actors to confirm it worked."
    print(f"\n🗣️ Prompt: {prompt}\n")
    
    # Execute the agent
    response = await agent.ainvoke({
        "messages": [HumanMessage(content=prompt)]
    })
    
    # Print Grok's final answer
    print("\n✅ Final Response:")
    print(response["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(run_unreal_agent())
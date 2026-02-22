import asyncio
import os
from langchain_mcp_adapters.client import MultiServerMCPClient

# 1. We brought back your favorite LLM provider!
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# The GROQ_API_KEY will now be automatically picked up from the environment by ChatGroq

async def run_unreal_agent():
    print("🤖 Booting up Llama 3 via Groq and connecting to Unreal Engine...")
    
    # Connect to your Unreal tools
    client = MultiServerMCPClient({
        "UnrealToy": {
            "transport": "sse",
            "url": "http://localhost:8000/sse"
        }
    })
        
    tools = await client.get_tools()
    print(f"🛠️  Loaded {len(tools)} tools from FastMCP.")
    
    # 2. Initialize Groq (using a highly capable tool-calling model)
    llm = ChatGroq(
        model="llama-3.3-70b-versatile", 
        temperature=0
    )
    
    # Create the Agent
    agent = create_agent(llm, tools)
    
    prompt = "Spawn a cube at X:0, Y:0, Z:100. Next, use the list_actors tool to find the full path of the cube you just spawned. Then, use the set_actor_scale tool to scale that exact cube to X:5.0, Y:5.0, Z:5.0 so it is huge and easy to see. Finally, tell me that it worked."
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
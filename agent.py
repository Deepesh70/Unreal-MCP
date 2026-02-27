import asyncio
import os
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

async def run_unreal_agent():
    print("🤖 Connecting to FastMCP Server...")
    
    # 1. Connect to your FastMCP server
    client = MultiServerMCPClient({
        "UnrealHPC": {
            "transport": "sse",
            "url": "http://localhost:8000/sse"
        }
    })
    
    tools = await client.get_tools()
    print(f"🛠️ Loaded {len(tools)} tools.")
    
    # 2. Initialize Qwen3:14b Local Model
    # Ensure Ollama is running (`ollama serve`) before executing this.
    llm = ChatOllama(
        model="qwen3:14b", 
        temperature=0.0, # 0.0 is critical for math and coding accuracy
        base_url="http://localhost:11434" 
    )
    
    # 3. The Strict HPC Prompt Template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a strict, logical Unreal Engine 3D architect. "
         "CRITICAL RULES:\n"
         "1. NO PARALLEL TOOL CALLING. Execute exactly ONE tool at a time.\n"
         "2. You MUST wait for the 'EXACT_ACTOR_PATH' from spawn_actor before applying transformations.\n"
         "3. If a tool fails, evaluate the error message and correct your parameters. Do not blindly repeat failed calls.\n"
         "4. Work procedurally. Think step-by-step before acting."
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    # 4. Create the ReAct Agent
    agent = create_tool_calling_agent(llm, tools, prompt_template)
    
    # max_iterations increased to handle the heavy multi-step logic of a colonnade
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=100)
    
    # 5. The Task Prompt (Optimized for Qwen and the new backend tools)
    task_prompt = r"""
    Construct a 3D circular colonnade consisting of exactly 6 pillars to test system stability.
    Radius: 1000 units around the origin (X:0, Y:0).
    
    For each of the 6 pillars (starting at 0 degrees, incrementing by 60 degrees):
    1. Calculate the coordinates: X = 1000 * cos(theta), Y = 1000 * sin(theta).
    2. Call `spawn_actor` using 'cylinder' at the calculated X, Y, and Z:0.
    3. WAIT for the exact path.
    4. Call `set_actor_transform` to scale the cylinder to (X:1.5, Y:1.5, Z:5.0) and confirm its location at your calculated X, Y, Z:0.
    5. Call `spawn_actor` using 'cube' at X, Y, and Z:500 (this is the cap).
    6. WAIT for the exact path.
    7. Call `set_actor_transform` to scale the cap to (X:2.0, Y:2.0, Z:0.2) at X, Y, Z:500.
    
    You must complete pillar 1 entirely before calculating or spawning pillar 2. Begin with pillar 1 at 0 degrees.
    """
    
    print("\n🚀 Executing Qwen3:14b Loop. Watch the terminal...\n")
    
    # 6. Execute the loop
    result = await agent_executor.ainvoke({"input": task_prompt})
    
    print("\n✅ Final Response:")
    print(result["output"])

if __name__ == "__main__":
    asyncio.run(run_unreal_agent())
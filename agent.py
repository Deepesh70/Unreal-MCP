import asyncio
import os
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
# from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

async def run_unreal_agent():
    print("🤖 Connecting to FastMCP Server...")
    
    # 1. Connect to your FastMCP server
    client = MultiServerMCPClient({
        "UnrealToy": {
            "transport": "sse",
            "url": "http://localhost:8000/sse"
        }
    })
    
    tools = await client.get_tools()
    print(f"🛠️ Loaded {len(tools)} tools.")
    
    # 2. Initialize Groq
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    # 3. Setup the strict Prompt Template (Requires agent_scratchpad)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are an Unreal Engine 3D architect. STRICT RULE: ABSOLUTELY NO PARALLEL TOOL CALLING. You must execute exactly ONE tool at a time. Never batch tool calls. If you need to spawn and scale, you must: 1. Call spawn_actor. 2. Stop generating and WAIT for the exact path. 3. Call set_actor_scale. If you guess a path like 'Path_Following_0', you fail."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    # 4. Create the Tool Calling Agent and Executor
    agent = create_tool_calling_agent(llm, tools, prompt_template)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=60)
    
    # 5. The raw prompt (r"") protects the math syntax
    task_prompt = r"Using the spawn_actor and set_actor_scale tools, construct a 3D circular colonnade. Calculate the coordinates to spawn 12 cubes in a perfect circle with a radius of 2000 units around the origin (X:0, Y:0). To do this, calculate the angle $\theta$ for each pillar (every 30 degrees, from 0 to 330) and use the formulas $X = 2000 \cdot \cos(\theta)$ and $Y = 2000 \cdot \sin(\theta)$. You MUST work sequentially. Spawn 1 cube at a calculated (X, Y) coordinate with a Z-height of 0. WAIT for the spawn_actor tool to return the EXACT_ACTOR_PATH. Immediately pass that exact path into the set_actor_scale tool to stretch the cube into a tall pillar (X:100.0, Y:100.0, Z:800.0). Then spawn a sphere on top at Z:800.0. Do not move to the next pillar until the current one is spawned, scaled, and topped. Do not write a Python script for me to run; execute the tool calls directly. Confirm when complete."
    
    print("\n🚀 Executing ReAct Loop. Watch the terminal for tool calls...\n")
    
    # 6. Execute the loop
    result = await agent_executor.ainvoke({"input": task_prompt})
    
    print("\n✅ Final Response:")
    print(result["output"])

if __name__ == "__main__":
    asyncio.run(run_unreal_agent())
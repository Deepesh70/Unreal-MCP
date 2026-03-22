import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
import sys

MCP_SERVER_CONFIG = {
    "UnrealMCP": {
        "transport": "sse",
        "url": "http://localhost:8000/sse",
    }
}

async def main():
    try:
        print("Initializing client...")
        client = MultiServerMCPClient(MCP_SERVER_CONFIG)
        
        # Test 1: Just get_tools
        print("Calling get_tools()...")
        # For an async context manager:
        async with client as c:
            tools = await c.get_tools()
            print(f"Loaded {len(tools)} tools!")
            print(tools)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from unreal_mcp.connection.websocket import send_ue_ws_command

async def test():
    try:
        await send_ue_ws_command("/test", "test_func")
    except Exception as e:
        print(f"Caught exact error output: {e}")

asyncio.run(test())


import asyncio
import websockets
import json

async def test_connection():
    uri = "ws://127.0.0.1:30020"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri, timeout=5) as websocket:
            print("Successfully connected to Unreal Engine WebSocket!")
            # Send a simple ping-like command
            payload = {
                "MessageName": "http",
                "Parameters": {
                    "Url": "/remote/object/call",
                    "Verb": "PUT",
                    "Body": {
                        "objectPath": "/Script/Engine.Default__KismetSystemLibrary",
                        "functionName": "GetDisplayName",
                        "parameters": {
                            "Object": "/Script/Engine.Default__KismetSystemLibrary"
                        }
                    }
                }
            }
            await websocket.send(json.dumps(payload))
            response = await websocket.recv()
            print(f"Response from Unreal: {response[:100]}...")
            return True
    except Exception as e:
        print(f"Failed to connect: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())

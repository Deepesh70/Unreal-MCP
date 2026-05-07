import asyncio
import json
import logging
import sys
import os

# Force UTF-8 for Windows terminals to prevent crashes
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Import the necessary functions from the existing agents
sys.path.append(os.getcwd())
from agents.processor import _handle_unreal_intent, log

logging.basicConfig(level=logging.INFO, format="%(message)s")

# Detailed Classroom Design with Interactive Door
blueprint = {
    "Intent": "Spawn",
    "ID": "Antigravity_Classroom_Interactive",
    "RequestedLoc": [4000, 0, 500],
    "Parameters": {
        "StructureType": "Composite"
    },
    "Parts": [
        # Floor & Ceiling (15m x 12m)
        {"Shape": "cube", "Offset": [0, 0, -5], "Scale": [15, 12, 0.1], "Label": "Floor", "material": "grey"},
        {"Shape": "cube", "Offset": [0, 0, 300], "Scale": [15, 12, 0.1], "Label": "Ceiling", "material": "white"},
        
        # Walls (Back, Right, Left)
        {"Shape": "cube", "Offset": [0, 600, 150], "Scale": [15, 0.2, 3], "Label": "Wall_Back", "material": "white"},
        {"Shape": "cube", "Offset": [750, 0, 150], "Scale": [0.2, 12, 3], "Label": "Wall_Right", "material": "white"},
        {"Shape": "cube", "Offset": [-750, 0, 150], "Scale": [0.2, 12, 3], "Label": "Wall_Left", "material": "white"},
        
        # Front Wall (Split into two pillars and a header to leave room for the door)
        # Pillar Left (6.5m wide)
        {"Shape": "cube", "Offset": [-425, -600, 150], "Scale": [6.5, 0.2, 3], "Label": "Front_Wall_Left", "material": "white"},
        # Pillar Right (6.5m wide)
        {"Shape": "cube", "Offset": [425, -600, 150], "Scale": [6.5, 0.2, 3], "Label": "Front_Wall_Right", "material": "white"},
        # Header (2m wide above the door)
        {"Shape": "cube", "Offset": [0, -600, 275], "Scale": [2, 0.2, 0.5], "Label": "Front_Wall_Header", "material": "white"},
        
        # THE INTERACTIVE DOOR
        {"Shape": "door", "Offset": [0, -600, 125], "Scale": [2, 0.2, 2.5], "Label": "Interactive_Door"},
        
        # Whiteboard (On Front Wall)
        {"Shape": "cube", "Offset": [0, -590, 160], "Scale": [6, 0.05, 2], "Label": "Whiteboard", "material": "white"},
        
        # Teacher's Desk
        {"Shape": "cube", "Offset": [0, -400, 40], "Scale": [1.5, 0.8, 0.8], "Label": "TeacherDesk", "material": "brown"}
    ]
}

async def main():
    print("🚀 Antigravity Direct Spawn Script - INTERACTIVE Edition")
    try:
        # Clear previous building first to keep the scene clean
        print("Cleaning up old structures...")
        await _handle_unreal_intent({"Intent": "ClearAll"})
        
        # Spawn the new interactive one
        print("Spawning interactive classroom...")
        result = await _handle_unreal_intent(blueprint)
        print("\n✅ Success!")
        print(result)
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

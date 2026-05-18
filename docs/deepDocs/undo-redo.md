Editor Transactions (Undo/Redo) Support
Changes Made
Added full support for Unreal Engine's transaction API, enabling instant Ctrl+Z (Undo/Redo) for all actions performed by the MCP agent in the live viewport.

Remote Control API Commands (send_ue_ws_command & send_ue_ws_property):

Injected "generateTransaction": True into the JSON payload for all Remote Control REST calls.
Any actor spawned, modified, or deleted via the standard MCP tools (e.g. spawning.py, modify.py) is now automatically wrapped by Unreal's native transaction system.
Python Execution (execute_python):

Modified the wrapper script generated for execute_python to run inside a Python with unreal.ScopedEditorTransaction("MCP Python Script"): context manager.
Now any complex logic or advanced math executed via the Python interpreter plugin is also fully reversible.
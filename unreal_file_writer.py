import os
import json

# --- CONFIGURATION (CHANGE THESE FOR YOUR PC) ---
UNREAL_SOURCE_DIR = r"C:\Path\To\Your\UnrealProject\Source\YourProjectName"
PROJECT_API_MACRO = "YOURPROJECTNAME_API" # e.g., UNREALMCP_API

def generate_unreal_classes(json_payload):
    try:
        data = json.loads(json_payload)
        class_name = data.get("ClassName")
        files = data.get("Files", [])

        print(f"Building Unreal C++ Class: {class_name}...")

        for file_obj in files:
            file_name = file_obj["FileName"]
            # Inject the correct Unreal export macro
            content = file_obj["Content"].replace("{{PROJECT_API}}", PROJECT_API_MACRO)
            
            file_path = os.path.join(UNREAL_SOURCE_DIR, file_name)
            
            # Write the file to the Unreal Source folder
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f" -> Saved: {file_name}")

        print("\nSuccess! Switch to Unreal Engine and press Ctrl+Alt+F11 to Live Compile.")

    except Exception as e:
        print(f"Failed to generate classes. Error: {e}")

# If you want to test it locally, you pass the JSON to this function.

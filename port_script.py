import os
import re

src_dir = r"E:\LyraStarterGame\Source\LyraGame"
dst_dir = r"E:\UE_Projects\Project_oo1\Source\Project_oo1"
build_cs_path = r"E:\UE_Projects\Project_oo1\Source\Project_oo1\Project_oo1.Build.cs"

files_to_copy = [
    "ProceduralCityManager.h",
    "ProceduralCityManager.cpp",
    "ProceduralBuildingTypes.h",
    "ProceduralBaseActor.h",
    "ProceduralBaseActor.cpp"
]

if not os.path.exists(dst_dir):
    print(f"Error: Destination directory {dst_dir} does not exist.")
    exit(1)

for file in files_to_copy:
    src_path = os.path.join(src_dir, file)
    dst_path = os.path.join(dst_dir, file)
    
    if not os.path.exists(src_path):
        print(f"Warning: {src_path} not found.")
        continue
        
    with open(src_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Replace LYRAGAME_API with PROJECT_OO1_API
    content = content.replace("LYRAGAME_API", "PROJECT_OO1_API")
    
    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Copied {file} and replaced API macro.")

# Now update Build.cs
if os.path.exists(build_cs_path):
    with open(build_cs_path, "r", encoding="utf-8") as f:
        build_content = f.read()
        
    modules_to_add = ['"Json"', '"JsonUtilities"', '"GeometryScriptingCore"']
    for mod in modules_to_add:
        if mod not in build_content:
            # Simple regex to inject into PublicDependencyModuleNames
            # Looks for: PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore" });
            pattern = r'(PublicDependencyModuleNames\.AddRange\(new string\[\] \{.*?)(?=\}\);)'
            replacement = r'\1, ' + mod + ' '
            build_content = re.sub(pattern, replacement, build_content, flags=re.DOTALL)
            print(f"Added {mod} to Build.cs")
            
    with open(build_cs_path, "w", encoding="utf-8") as f:
        f.write(build_content)
else:
    print(f"Warning: Could not find {build_cs_path}")

print("SUCCESS: Porting completed!")

import os
import sys
import json
import subprocess
import winreg

def get_engine_path(engine_association):
    """Find the Unreal Engine installation path from the registry based on EngineAssociation."""
    # Custom builds usually have a GUID as association. Epic launcher builds have "5.3", "5.4", etc.
    try:
        # Check Epic Games registry
        key_path = rf"SOFTWARE\EpicGames\Unreal Engine\{engine_association}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            installed_directory, _ = winreg.QueryValueEx(key, "InstalledDirectory")
            return installed_directory
    except WindowsError:
        pass

    try:
        # Check custom builds (GUIDs) in HKCU
        key_path = rf"Software\Epic Games\Unreal Engine\Builds"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            installed_directory, _ = winreg.QueryValueEx(key, engine_association)
            return installed_directory
    except WindowsError:
        pass

    # Fallback to common path
    common_path = rf"C:\Program Files\Epic Games\UE_{engine_association}"
    if os.path.exists(common_path):
        return common_path

    # Fallback to other drives
    for drive in ["D:", "E:"]:
        common_path = rf"{drive}\Epic Games\UE_{engine_association}"
        if os.path.exists(common_path):
            return common_path

    return None

def clean_generated_files(uproject_path):
    """Delete generated C++ files on fatal error."""
    project_dir = os.path.dirname(uproject_path)
    project_name = os.path.splitext(os.path.basename(uproject_path))[0]
    source_dir = os.path.join(project_dir, "Source", project_name)
    
    files_to_remove = [
        "ProceduralBuildingTypes.h",
        "ProceduralCityManager.h",
        "ProceduralCityManager.cpp",
    ]
    
    print("\n  🧹 Automated Garbage Collection: Fatal compile error detected!")
    print("     Deleting corrupted generated files to restore project...")
    
    for filename in files_to_remove:
        path = os.path.join(source_dir, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"     ✅ Removed {filename}")
            except Exception as e:
                print(f"     ❌ Failed to remove {filename}: {e}")

def run_headless_compile(uproject_path):
    """Run the headless compiler and catch fatal errors."""
    if not os.path.exists(uproject_path):
        print(f"❌ Project not found: {uproject_path}")
        return False
        
    try:
        with open(uproject_path, "r", encoding="utf-8") as f:
            uproject_data = json.load(f)
            engine_association = uproject_data.get("EngineAssociation")
    except Exception as e:
        print(f"❌ Failed to parse .uproject: {e}")
        return False
        
    if not engine_association:
        print("❌ Could not determine EngineAssociation from .uproject")
        return False
        
    engine_path = get_engine_path(engine_association)
    if not engine_path:
        print(f"❌ Could not find Unreal Engine installation for version {engine_association}")
        return False
        
    build_bat = os.path.join(engine_path, "Engine", "Build", "BatchFiles", "Build.bat")
    if not os.path.exists(build_bat):
        print(f"❌ Could not find Build.bat at {build_bat}")
        return False
        
    project_name = os.path.splitext(os.path.basename(uproject_path))[0]
    
    # Run UnrealBuildTool
    # Example: Build.bat MyProjectEditor Win64 Development -Project="C:\Path\MyProject.uproject" -WaitMutex
    cmd = [
        build_bat,
        f"{project_name}Editor",
        "Win64",
        "Development",
        f"-Project={os.path.abspath(uproject_path)}",
        "-WaitMutex"
    ]
    
    print(f"\n🚀 Running Headless Compiler (UBT) for {project_name}...")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        # Run with Popen to capture output
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        
        fatal_error_detected = False
        
        for line in iter(process.stdout.readline, ''):
            sys.stdout.write(line)
            sys.stdout.flush()
            
            # Check for fatal errors
            if "LNK2019" in line or "C1083" in line or "error C2" in line or "fatal error" in line.lower():
                fatal_error_detected = True
                
        process.wait()
        
        if fatal_error_detected or process.returncode != 0:
            print("\n❌ Compilation failed!")
            clean_generated_files(uproject_path)
            return False
            
        print("\n✅ Compilation successful!")
        return True
        
    except Exception as e:
        print(f"❌ Exception during compilation: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compile_and_clean.py <path_to_uproject>")
        sys.exit(1)
        
    success = run_headless_compile(sys.argv[1])
    sys.exit(0 if success else 1)

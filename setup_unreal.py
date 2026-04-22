"""
setup_unreal.py — One-click Unreal project integration script.

Finds your .uproject file, copies the generated C++ to the correct
Source directory, replaces {{PROJECT_API}} with the right macro,
adds Json/JsonUtilities to Build.cs, and tells you what to do next.

Usage:
    python setup_unreal.py                          # Auto-scan for .uproject
    python setup_unreal.py D:/MyGame/MyGame.uproject  # Specify path directly
"""

import os
import sys
import re
import shutil
import glob

# Fix Windows console encoding for emoji/unicode
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def find_uproject(search_root=None):
    """Search for .uproject files on common drives."""
    if search_root:
        for root, dirs, files in os.walk(search_root):
            for f in files:
                if f.endswith('.uproject'):
                    return os.path.join(root, f)
        return None

    # Search common locations
    search_paths = [
        os.path.expanduser("~\\Documents\\Unreal Projects"),
        os.path.expanduser("~\\Desktop"),
        "D:\\",
        "E:\\",
        "C:\\Users",
    ]

    # Quick scan — only check 3 levels deep
    found = []
    for base in search_paths:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            depth = root.replace(base, '').count(os.sep)
            if depth > 3:
                dirs.clear()
                continue
            for f in files:
                if f.endswith('.uproject'):
                    found.append(os.path.join(root, f))

    return found


def get_project_name(uproject_path):
    """Extract the project name from the .uproject filename."""
    return os.path.splitext(os.path.basename(uproject_path))[0]


def get_source_dir(uproject_path):
    """Get the Source/<ProjectName>/ directory."""
    project_name = get_project_name(uproject_path)
    project_dir = os.path.dirname(uproject_path)
    return os.path.join(project_dir, "Source", project_name)


def get_build_cs_path(uproject_path):
    """Get the Build.cs file path."""
    project_name = get_project_name(uproject_path)
    source_dir = get_source_dir(uproject_path)
    return os.path.join(source_dir, f"{project_name}.Build.cs")


def replace_project_api(content, project_name):
    """Replace {{PROJECT_API}} with the actual macro."""
    api_macro = f"{project_name.upper()}_API"
    return content.replace("{{PROJECT_API}}", api_macro)


def patch_build_cs(build_cs_path):
    """Add Json and JsonUtilities to the Build.cs if not already there."""
    if not os.path.exists(build_cs_path):
        print(f"  ⚠️  Build.cs not found at: {build_cs_path}")
        print(f"      You must manually add \"Json\", \"JsonUtilities\" to PublicDependencyModuleNames.")
        return False

    with open(build_cs_path, "r", encoding="utf-8") as f:
        content = f.read()

    if '"Json"' in content and '"JsonUtilities"' in content:
        print("  ✅ Build.cs already has Json + JsonUtilities.")
        return True

    # Find the PublicDependencyModuleNames line and add our modules
    pattern = r'(PublicDependencyModuleNames\.AddRange\s*\(\s*new\s*string\s*\[\]\s*\{[^}]*)'
    match = re.search(pattern, content)
    if match:
        existing = match.group(1)
        if '"Json"' not in content:
            # Add before the closing brace
            patched = existing.rstrip().rstrip(',') + ', "Json", "JsonUtilities"'
            content = content.replace(existing, patched)

            with open(build_cs_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("  ✅ Added \"Json\", \"JsonUtilities\" to Build.cs")
            return True
    else:
        print(f"  ⚠️  Could not auto-patch Build.cs. Please manually add:")
        print(f'      "Json", "JsonUtilities" to PublicDependencyModuleNames')
        return False


def main():
    print("\n" + "=" * 60)
    print("  🏗️  Unreal-MCP Setup — One-Click C++ Integration")
    print("=" * 60 + "\n")

    # ── Step 1: Find .uproject ───────────────────────────────────
    uproject_path = None

    if len(sys.argv) > 1:
        uproject_path = sys.argv[1]
        if not os.path.exists(uproject_path):
            print(f"❌ File not found: {uproject_path}")
            sys.exit(1)
    else:
        print("🔍 Searching for Unreal projects...")
        found = find_uproject()

        if not found:
            print("❌ No .uproject files found.")
            print("   Usage: python setup_unreal.py D:\\MyGame\\MyGame.uproject")
            sys.exit(1)

        if isinstance(found, list):
            if len(found) == 1:
                uproject_path = found[0]
            else:
                print(f"\n📂 Found {len(found)} Unreal projects:\n")
                for i, p in enumerate(found):
                    print(f"  [{i + 1}] {p}")
                print()
                choice = input("Pick a number (or press Enter for #1): ").strip()
                idx = int(choice) - 1 if choice.isdigit() else 0
                uproject_path = found[idx]
        else:
            uproject_path = found

    project_name = get_project_name(uproject_path)
    api_macro = f"{project_name.upper()}_API"
    source_dir = get_source_dir(uproject_path)
    project_dir = os.path.dirname(uproject_path)

    print(f"\n📁 Project: {project_name}")
    print(f"   Path:    {project_dir}")
    print(f"   API:     {api_macro}")
    print(f"   Source:  {source_dir}\n")

    # ── Step 2: Copy C++ files ───────────────────────────────────
    generated_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated")
    cpp_files = [
        "ProceduralBuildingTypes.h",
        "ProceduralCityManager.h",
        "ProceduralCityManager.cpp",
    ]

    os.makedirs(source_dir, exist_ok=True)

    print("📋 Copying C++ files...")
    for filename in cpp_files:
        src = os.path.join(generated_dir, filename)
        if not os.path.exists(src):
            print(f"  ❌ Missing: {src}")
            continue

        with open(src, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace the placeholder with the real API macro
        content = replace_project_api(content, project_name)

        dst = os.path.join(source_dir, filename)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ {filename} → {dst}")

    # ── Step 3: Patch Build.cs ───────────────────────────────────
    print("\n🔧 Patching Build.cs...")
    build_cs = get_build_cs_path(uproject_path)
    patch_build_cs(build_cs)

    # ── Step 4: Update .env ──────────────────────────────────────
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    print("\n📝 Updating .env...")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            env_content = f.read()
        if "PROJECT_API" not in env_content:
            with open(env_path, "a", encoding="utf-8") as f:
                f.write(f"\n# Unreal project API macro\nPROJECT_API={api_macro}\n")
            print(f"  ✅ Added PROJECT_API={api_macro} to .env")
        else:
            print(f"  ℹ️  PROJECT_API already in .env (not overwriting)")
    else:
        print(f"  ⚠️  No .env file found — create one from .env.example")

    # ── Done ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  ✅ SETUP COMPLETE!")
    print("=" * 60)
    print(f"""
  WHAT TO DO NOW:
  ───────────────
  1. Open {project_name}.uproject in Unreal Editor
  2. Let it compile the C++ (or click Build if prompted)
  3. In Content Browser, search "ProceduralCityManager"
  4. Drag it into your level → Save the level
  5. Make sure "Remote Control API" plugin is enabled
     (Edit → Plugins → search "Remote Control")

  THEN RUN:
  ─────────
  Terminal 1:  python server.py
  Terminal 2:  python agent.py gemini -b -i

  🏗️ Builder > build a 3-story house with a pointed roof
  🏗️ Builder > build a city block with 5 buildings
  🏗️ Builder > clear everything

  Your building will appear in the Unreal viewport. ✅
""")


if __name__ == "__main__":
    main()

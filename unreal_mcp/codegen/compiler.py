import subprocess
import os
import sys
from unreal_mcp.config.settings import (
    UE_BATCH_FILES_PATH, 
    UE_PROJECT_FILE_PATH, 
    UE_PROJECT_NAME
)

def run_headless_compile_check() -> tuple[bool, str]:
    """
    Triggers a background UBT build. 
    Returns: (Success Boolean, Error Log String)
    """
    # Build.bat <ProjectName>Editor Win64 Development <PathToUProject> -waitmutex
    # -waitmutex is CRITICAL: it prevents collision if your Unreal Editor is already open.
    cmd = [
        UE_BATCH_FILES_PATH,
        f"{UE_PROJECT_NAME}Editor",
        "Win64",
        "Development",
        UE_PROJECT_FILE_PATH,
        "-waitmutex"
    ]

    print(f"\n  [CI/CD] Launching Headless Compiler for {UE_PROJECT_NAME}...")
    
    try:
        # Start the process and capture output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            encoding='utf-8',
            errors='replace'
        )

        full_log = ""
        # Stream the output live so you can see if it's hanging
        for line in process.stdout:
            full_log += line
            # Print only errors or progress to keep the console clean
            if "error" in line.lower() or "failed" in line.lower():
                print(f"    [!] {line.strip()}")
            elif "Compiling" in line:
                print(f"    [>] {line.strip()}")

        process.wait()

        if process.returncode == 0:
            return True, "Success"
        else:
            # We only want the actual C++ errors (C2143, etc.) to save LLM tokens
            error_lines = [l for l in full_log.split('\n') if "error" in l.lower() or " : " in l]
            # Grab the last 15 lines of errors—usually where the root cause sits
            return False, "\n".join(error_lines[-15:])

    except Exception as e:
        return False, f"Subprocess failed to launch UBT: {str(e)}"
import subprocess
import os
import sys
import time
from pathlib import Path
from unreal_mcp.config.settings import (
    UE_BATCH_FILES_PATH, 
    UE_PROJECT_FILE_PATH, 
    UE_PROJECT_NAME,
    UE_PROJECT_ROOT,
    UE_EDITOR_EXE_PATH,
    ORCH_EDITOR_CLOSE_TIMEOUT_SEC,
)


def _list_running_process_names() -> set[str]:
    """Best-effort process listing for preflight checks."""
    names: set[str] = set()
    try:
        if sys.platform == "win32":
            out = subprocess.check_output(
                ["tasklist", "/FO", "CSV", "/NH"],
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for line in out.splitlines():
                line = line.strip()
                if not line:
                    continue
                # CSV row format begins with process image name.
                if line.startswith('"'):
                    image = line.split('","', 1)[0].strip('"')
                else:
                    image = line.split(",", 1)[0].strip('"')
                if image:
                    names.add(image.lower())
            return names

        out = subprocess.check_output(["ps", "-A", "-o", "comm="], text=True, encoding="utf-8", errors="replace")
        for line in out.splitlines():
            proc = Path(line.strip()).name
            if proc:
                names.add(proc.lower())
    except Exception:
        return set()
    return names


def _is_unreal_editor_running() -> bool:
    """Detect if UnrealEditor is currently running."""
    process_names = _list_running_process_names()
    if not process_names:
        return False

    editor_markers = (
        "unrealeditor.exe",
        "unrealeditor-cmd.exe",
        "ue4editor.exe",
        "ue4editor-cmd.exe",
    )
    return any(name in process_names for name in editor_markers)


def is_unreal_editor_running() -> bool:
    """Public wrapper to check Unreal Editor process state."""
    return _is_unreal_editor_running()


def stop_unreal_editor(force: bool = False, timeout_seconds: int | None = None) -> tuple[bool, str]:
    """
    Attempt to stop Unreal Editor processes.

    Args:
        force: When True, force-kill if graceful close does not finish in time.
        timeout_seconds: Max wait before optional force kill.
    """
    if timeout_seconds is None:
        timeout_seconds = ORCH_EDITOR_CLOSE_TIMEOUT_SEC

    if not _is_unreal_editor_running():
        return True, "Unreal Editor is not running."

    # Best-effort graceful close first.
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/IM", "UnrealEditor.exe", "/T"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            subprocess.run(
                ["taskkill", "/IM", "UE4Editor.exe", "/T"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        else:
            subprocess.run(["pkill", "-TERM", "-f", "UnrealEditor"], capture_output=True, text=True)
            subprocess.run(["pkill", "-TERM", "-f", "UE4Editor"], capture_output=True, text=True)
    except Exception as e:
        return False, f"Failed to issue graceful close command: {e}"

    deadline = time.time() + max(1, timeout_seconds)
    while time.time() < deadline:
        if not _is_unreal_editor_running():
            return True, "Unreal Editor closed gracefully."
        time.sleep(1)

    if not force:
        return False, (
            "Unreal Editor did not close before timeout. "
            "Retry with force=True or close it manually."
        )

    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/IM", "UnrealEditor.exe", "/T"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            subprocess.run(
                ["taskkill", "/F", "/IM", "UE4Editor.exe", "/T"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        else:
            subprocess.run(["pkill", "-KILL", "-f", "UnrealEditor"], capture_output=True, text=True)
            subprocess.run(["pkill", "-KILL", "-f", "UE4Editor"], capture_output=True, text=True)
    except Exception as e:
        return False, f"Force-kill command failed: {e}"

    if _is_unreal_editor_running():
        return False, "Unreal Editor is still running after force-close attempt."
    return True, "Unreal Editor force-closed."


def start_unreal_editor(startup_map: str | None = None) -> tuple[bool, str]:
    """Launch Unreal Editor for the configured project."""
    if not Path(UE_EDITOR_EXE_PATH).exists():
        return False, f"UnrealEditor.exe not found: {UE_EDITOR_EXE_PATH}"

    if not Path(UE_PROJECT_FILE_PATH).exists():
        return False, f".uproject not found: {UE_PROJECT_FILE_PATH}"

    cmd = [UE_EDITOR_EXE_PATH, UE_PROJECT_FILE_PATH]
    if startup_map:
        cmd.append(startup_map)

    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        return True, "Unreal Editor launch command issued."
    except Exception as e:
        return False, f"Failed to launch Unreal Editor: {e}"


def _find_live_coding_patch_artifacts(limit: int = 10) -> list[Path]:
    """Find common Live Coding patch outputs that can poison linker state."""
    roots = [
        Path(UE_PROJECT_ROOT) / "Binaries",
        Path(UE_PROJECT_ROOT) / "Plugins",
    ]

    found: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        try:
            for pattern in ("*.patch_*.exe", "*.patch_*", "*LiveCoding*.dll"):
                for path in root.rglob(pattern):
                    key = str(path).lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    found.append(path)
                    if len(found) >= limit:
                        return found
        except Exception:
            # Best-effort scan only.
            continue
    return found


def run_compile_preflight_check() -> tuple[bool, str]:
    """
    Validate build environment before running expensive LLM+compile retries.

    Returns:
      (True, 'ok') if environment looks healthy, else (False, human-readable report).
    """
    issues = []

    if not Path(UE_BATCH_FILES_PATH).exists():
        issues.append(f"Build.bat not found: {UE_BATCH_FILES_PATH}")

    if not Path(UE_PROJECT_FILE_PATH).exists():
        issues.append(f".uproject not found: {UE_PROJECT_FILE_PATH}")

    source_dir = Path(UE_PROJECT_ROOT) / "Source" / UE_PROJECT_NAME
    if not source_dir.exists():
        issues.append(f"Source directory not found: {source_dir}")

    if _is_unreal_editor_running():
        issues.append("UnrealEditor.exe is running. Close the editor before headless CI/CD compile.")

    # Live coding patch artifacts can poison headless link/compile retries.
    patch_artifacts = _find_live_coding_patch_artifacts()
    if patch_artifacts:
        sample = "\n".join(f"  - {p}" for p in patch_artifacts[:5])
        issues.append(
            "Detected Live Coding patch artifacts that can break clean compile. "
            "Delete these files and retry:\n" + sample
        )

    if issues:
        remediation = (
            "Compile preflight failed:\n"
            + "\n".join(f"- {i}" for i in issues)
            + "\n\nRemediation:\n"
            + "1. Close Unreal Editor.\n"
            + "2. Delete Live Coding patch artifacts under project Binaries/ and Plugins/ Binaries.\n"
            + "3. Verify UE path/project path in unreal_mcp/config/settings.py.\n"
            + "4. Re-run the pipeline."
        )
        return False, remediation

    return True, "ok"


def _read_latest_unreal_log_tail(max_lines: int = 80) -> str:
    """Read tail lines from the most recent Unreal log under Saved/Logs."""
    try:
        logs_dir = Path(UE_PROJECT_ROOT) / "Saved" / "Logs"
        if not logs_dir.exists():
            return ""

        log_files = sorted(logs_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not log_files:
            return ""

        latest = log_files[0]
        text = latest.read_text(encoding="utf-8", errors="replace")
        lines = [l for l in text.splitlines() if l.strip()]

        interesting = []
        for line in lines:
            low = line.lower()
            if "error" in low or "fatal" in low or "uht" in low or "compilation" in low:
                interesting.append(line.strip())

        if interesting:
            return "\n".join(interesting[-max_lines:])

        return "\n".join(lines[-max_lines:])
    except Exception:
        return ""

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
        "-waitmutex",
        "-NoHotReloadFromIDE",
        "-NoLiveCoding",
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
            lines = full_log.split('\n')

            # Extract actionable diagnostics first.
            diagnostics = []
            patterns = (
                "error C",          # MSVC compile error, e.g., error C2143
                ": error",          # Generic compiler/UHT error format
                "fatal error",      # Fatal compile/include errors
                "unrecognized type",# UHT parser errors
                "UHT Error",        # UnrealHeaderTool explicit error
                "OtherCompilationError",
            )

            for line in lines:
                low = line.lower()
                if any(p.lower() in low for p in patterns):
                    cleaned = line.strip()
                    if cleaned:
                        diagnostics.append(cleaned)

            # If no focused diagnostics were found, fall back to tail of the build log.
            if not diagnostics:
                tail = [l.strip() for l in lines[-40:] if l.strip()]
                diagnostics = tail

            # Deduplicate while preserving order and keep output compact.
            seen = set()
            compact = []
            for d in diagnostics:
                if d not in seen:
                    compact.append(d)
                    seen.add(d)

            message = "\n".join(compact[-30:])

            # If output is still generic, pull Unreal Saved/Logs tail for actionable details.
            if "OtherCompilationError" in message and "error C" not in message:
                log_tail = _read_latest_unreal_log_tail()
                if log_tail:
                    message += "\n\n[Unreal Log Tail]\n" + log_tail

            return False, message

    except Exception as e:
        return False, f"Subprocess failed to launch UBT: {str(e)}"

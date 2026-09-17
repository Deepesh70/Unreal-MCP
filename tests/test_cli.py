import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def test_cli_help():
    """Verify unreal-mcp CLI displays help without errors."""
    result = subprocess.run(
        [sys.executable, "-m", "unreal_mcp.cli", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower() or "unreal-mcp" in result.stdout.lower()


def test_cli_subcommand_agent_help():
    """Verify unreal-mcp agent shows usage when invoked without backend."""
    result = subprocess.run(
        [sys.executable, "-m", "unreal_mcp.cli", "agent"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=PROJECT_ROOT,
    )
    assert result.stdout is not None
    assert "Unreal MCP Agent Launcher" in result.stdout or "Usage:" in result.stdout


if __name__ == "__main__":
    test_cli_help()
    test_cli_subcommand_agent_help()
    print("All CLI tests passed successfully!")

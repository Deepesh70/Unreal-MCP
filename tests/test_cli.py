import subprocess
import sys


def test_cli_help():
    """Verify unreal-mcp CLI displays help without errors."""
    result = subprocess.run(
        [sys.executable, "-m", "unreal_mcp.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower() or "unreal-mcp" in result.stdout.lower()

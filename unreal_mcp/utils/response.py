"""
Response Parsing & Formatting Utilities.

Shared helpers that multiple MCP tools use to interpret Unreal Engine
responses and build human-readable output strings.
"""


def extract_return_value(response: dict) -> any:
    """
    Pull the ReturnValue out of a nested WebSocket response.

    Unreal wraps everything in:
        { "ResponseBody": { "ReturnValue": <actual data> } }

    Args:
        response: The full parsed JSON from `send_ue_ws_command()`.

    Returns:
        The raw ReturnValue (could be a list, dict, string, etc.),
        or an empty list if the key is missing.
    """
    return response.get("ResponseBody", {}).get("ReturnValue", [])


def format_actor_list(actors: list[str]) -> str:
    """
    Format a list of actor object-path strings into readable output.

    Each actor path looks like:
        /Game/Level.Level:PersistentLevel.StaticMeshActor_0

    We extract the short name (after the last dot) and display both.

    Args:
        actors: A list of full Unreal object path strings.

    Returns:
        A newline-separated string with name + path for each actor,
        or a "No actors found" message if the list is empty.
    """
    if not actors:
        return "No actors found or list is empty."

    lines = [f"{a.split('.')[-1]} (Path: {a})" for a in actors]
    return "Actors in level:\n" + "\n".join(lines)


def format_error(error: Exception, tip: str = "") -> str:
    """
    Build a standardised error message with an optional troubleshooting tip.

    Args:
        error: The caught exception.
        tip:   Optional one-liner hint for the user / LLM agent.

    Returns:
        A formatted error string.
    """
    msg = f"Error: {str(error)}"
    if tip:
        msg += f". Tip: {tip}"
    return msg

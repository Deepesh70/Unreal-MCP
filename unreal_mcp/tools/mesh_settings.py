"""
Mesh Settings Tool — edit mesh component properties in Unreal.

Supports bulk property updates and discovery so the agent can modify
multiple settings on a specific mesh reliably.
"""

from difflib import get_close_matches
from typing import Any, Dict, List, Optional, Set, Tuple

from unreal_mcp import mcp
from unreal_mcp.connection import (
    send_ue_ws_object_describe,
    send_ue_ws_property_read,
    send_ue_ws_property_update,
)
from unreal_mcp.utils import format_error


def _candidate_mesh_paths(actor_or_mesh_path: str) -> List[str]:
    """
    Build likely mesh component object paths from an actor path.

    If a mesh component path is already provided, the first candidate
    will be the exact input and Unreal will accept it directly.
    """
    path = actor_or_mesh_path.strip()
    return [
        path,
        f"{path}.StaticMeshComponent0",
        f"{path}.StaticMeshComponent",
        f"{path}.Mesh",
    ]


def _collect_property_names(payload: Any) -> Set[str]:
    """Recursively extract likely property-name fields from a describe payload."""
    names: Set[str] = set()

    if isinstance(payload, dict):
        for key, value in payload.items():
            key_l = str(key).lower()

            if key_l in {"propertyname", "name", "displayname"} and isinstance(value, str):
                if value and not value.startswith("/"):
                    names.add(value)

            if key_l in {"properties", "fields", "members", "propertydescriptions"}:
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            prop_name = (
                                item.get("Name")
                                or item.get("PropertyName")
                                or item.get("DisplayName")
                                or item.get("name")
                                or item.get("propertyName")
                                or item.get("displayName")
                            )
                            if isinstance(prop_name, str) and prop_name:
                                names.add(prop_name)

            names.update(_collect_property_names(value))

    elif isinstance(payload, list):
        for item in payload:
            names.update(_collect_property_names(item))

    return names


async def _discover_mesh_property_names(actor_or_mesh_path: str) -> Tuple[Optional[str], List[str], Optional[str]]:
    """
    Discover valid property names for a mesh object path.

    Returns:
      (resolved_path, sorted_property_names, last_error)
    """
    candidates = _candidate_mesh_paths(actor_or_mesh_path)
    last_error = None

    for candidate_path in candidates:
        try:
            response = await send_ue_ws_object_describe(candidate_path)
            names = sorted(_collect_property_names(response))
            if names:
                return candidate_path, names, None
            last_error = f"No properties in describe payload for {candidate_path}"
        except Exception as e:
            last_error = str(e)

    return None, [], last_error


@mcp.tool()
async def list_mesh_settings(
    actor_or_mesh_path: str,
    contains: str = "",
    limit: int = 120,
) -> str:
    """
    Discover valid mesh setting/property names from Unreal for this mesh.

    Args:
        actor_or_mesh_path: Actor path or mesh component path.
        contains: Optional case-insensitive filter substring.
        limit: Max number of property names to return.
    """
    try:
        resolved_path, names, last_error = await _discover_mesh_property_names(actor_or_mesh_path)
        if not names:
            return (
                "Error: Could not discover mesh settings. "
                f"Path tried: {actor_or_mesh_path}. Last error: {last_error}"
            )

        filter_text = contains.strip().lower()
        filtered = [n for n in names if filter_text in n.lower()] if filter_text else names

        max_items = max(1, min(int(limit), 500))
        shown = filtered[:max_items]

        suffix = ""
        if len(filtered) > len(shown):
            suffix = f"\n... and {len(filtered) - len(shown)} more"

        title = f"Mesh settings for {resolved_path} ({len(filtered)} match, {len(names)} total):"
        return title + "\n" + "\n".join(shown) + suffix
    except Exception as e:
        return format_error(e, "Check actor_or_mesh_path and ensure Unreal Remote Control is running.")


@mcp.tool()
async def validate_mesh_settings(
    actor_or_mesh_path: str,
    setting_names: List[str],
) -> str:
    """
    Validate mesh setting names against live Unreal metadata.

    Returns which names are valid and close suggestions for invalid names.
    """
    try:
        if not setting_names:
            return "Error: setting_names must contain at least one property name."

        resolved_path, names, last_error = await _discover_mesh_property_names(actor_or_mesh_path)
        if not names:
            return (
                "Error: Could not validate settings because discovery failed. "
                f"Last error: {last_error}"
            )

        known = set(names)
        valid = []
        invalid = []

        for raw in setting_names:
            name = str(raw)
            if name in known:
                valid.append(name)
            else:
                suggestions = get_close_matches(name, names, n=3, cutoff=0.55)
                invalid.append((name, suggestions))

        lines = [f"Validation target: {resolved_path}"]
        if valid:
            lines.append("Valid: " + ", ".join(valid))
        if invalid:
            for bad, suggestions in invalid:
                if suggestions:
                    lines.append(f"Invalid: {bad} -> maybe: {', '.join(suggestions)}")
                else:
                    lines.append(f"Invalid: {bad}")

        return "\n".join(lines)
    except Exception as e:
        return format_error(e, "Use an actor path from list_actors and property names as plain strings.")


@mcp.tool()
async def read_mesh_settings(
    actor_or_mesh_path: str,
    setting_names: List[str],
) -> str:
    """
    Read current values for one or more mesh settings from Unreal.

    Args:
        actor_or_mesh_path: Actor path or mesh component path.
        setting_names: List of exact Unreal property names to read.
    """
    try:
        if not setting_names:
            return "Error: setting_names must contain at least one property name to read."

        resolved_path, known_names, last_error = await _discover_mesh_property_names(actor_or_mesh_path)
        if not resolved_path:
            return (
                "Error: Could not resolve mesh path for reading settings. "
                f"Last error: {last_error}"
            )

        values: Dict[str, Any] = {}
        failures: List[str] = []

        for raw_name in setting_names:
            prop_name = str(raw_name)
            try:
                response = await send_ue_ws_property_read(
                    object_path=resolved_path,
                    property_name=prop_name,
                )

                body = response.get("ResponseBody", {}) if isinstance(response, dict) else {}

                if "PropertyValue" in body:
                    values[prop_name] = body.get("PropertyValue")
                elif "ReturnValue" in body:
                    values[prop_name] = body.get("ReturnValue")
                elif isinstance(body, dict):
                    values[prop_name] = body
                else:
                    values[prop_name] = None

            except Exception as e:
                suggestions = get_close_matches(prop_name, known_names, n=3, cutoff=0.55)
                if suggestions:
                    failures.append(f"{prop_name} ({e}) -> maybe: {', '.join(suggestions)}")
                else:
                    failures.append(f"{prop_name} ({e})")

        lines = [f"Read mesh settings from {resolved_path}:"]
        if values:
            for key in setting_names:
                k = str(key)
                if k in values:
                    lines.append(f"{k}: {values[k]}")
        if failures:
            lines.append("Failed: " + "; ".join(failures))

        return "\n".join(lines)

    except Exception as e:
        return format_error(e, "Use a valid actor_or_mesh_path and exact property names.")


@mcp.tool()
async def sync_mesh_settings(
    actor_or_mesh_path: str,
    desired_settings: Dict[str, Any],
) -> str:
    """
    Compare current mesh settings against desired values and apply only diffs.

    Args:
        actor_or_mesh_path: Actor path or mesh component path.
        desired_settings: Desired Unreal property values.
    """
    try:
        if not isinstance(desired_settings, dict) or not desired_settings:
            return "Error: desired_settings must be a non-empty object of property:value pairs."

        resolved_path, known_names, last_error = await _discover_mesh_property_names(actor_or_mesh_path)
        if not resolved_path:
            return (
                "Error: Could not resolve mesh path for sync. "
                f"Last error: {last_error}"
            )

        updated: List[str] = []
        unchanged: List[str] = []
        failed: List[str] = []

        for raw_name, desired_value in desired_settings.items():
            prop_name = str(raw_name)
            try:
                response = await send_ue_ws_property_read(
                    object_path=resolved_path,
                    property_name=prop_name,
                )
                body = response.get("ResponseBody", {}) if isinstance(response, dict) else {}

                if "PropertyValue" in body:
                    current_value = body.get("PropertyValue")
                elif "ReturnValue" in body:
                    current_value = body.get("ReturnValue")
                else:
                    current_value = None

                if current_value == desired_value:
                    unchanged.append(prop_name)
                    continue

                await send_ue_ws_property_update(
                    object_path=resolved_path,
                    property_name=prop_name,
                    property_value=desired_value,
                )
                updated.append(prop_name)

            except Exception as e:
                suggestions = get_close_matches(prop_name, known_names, n=3, cutoff=0.55)
                if suggestions:
                    failed.append(f"{prop_name} ({e}) -> maybe: {', '.join(suggestions)}")
                else:
                    failed.append(f"{prop_name} ({e})")

        lines = [f"Synced mesh settings on {resolved_path}:"]
        if updated:
            lines.append("Updated: " + ", ".join(updated))
        if unchanged:
            lines.append("Already matched: " + ", ".join(unchanged))
        if failed:
            lines.append("Failed: " + "; ".join(failed))

        return "\n".join(lines)

    except Exception as e:
        return format_error(e, "Use a valid actor_or_mesh_path and exact property names.")


@mcp.tool()
async def set_mesh_settings(
    actor_or_mesh_path: str,
    settings: Dict[str, Any],
) -> str:
    """
    Update one or more Unreal mesh properties for a specific mesh.

    Args:
        actor_or_mesh_path: Actor path or mesh component path.
        settings: Dict of Unreal property names to values.
    """
    try:
        if not isinstance(settings, dict) or not settings:
            return "Error: 'settings' must be a non-empty object of property:value pairs."

        candidates = _candidate_mesh_paths(actor_or_mesh_path)
        updated = []
        failed = []
        resolved_path = None
        _, known_names, _ = await _discover_mesh_property_names(actor_or_mesh_path)

        for prop_name, value in settings.items():
            prop_updated = False
            last_error = None

            for candidate_path in candidates:
                try:
                    await send_ue_ws_property_update(
                        object_path=candidate_path,
                        property_name=str(prop_name),
                        property_value=value,
                    )
                    prop_updated = True
                    resolved_path = candidate_path
                    updated.append(str(prop_name))
                    break
                except Exception as e:
                    last_error = str(e)

            if not prop_updated:
                prop_suggestions = get_close_matches(str(prop_name), known_names, n=3, cutoff=0.55)
                if prop_suggestions:
                    failed.append(f"{prop_name} ({last_error}) -> maybe: {', '.join(prop_suggestions)}")
                else:
                    failed.append(f"{prop_name} ({last_error})")

        if updated and not failed:
            return (
                f"Updated {len(updated)} mesh setting(s) on {resolved_path}: "
                + ", ".join(updated)
            )

        if updated and failed:
            return (
                f"Partially updated mesh settings on {resolved_path}: "
                + ", ".join(updated)
                + ". Failed: "
                + "; ".join(failed)
            )

        return "Error: Could not update any mesh settings. Verify actor_or_mesh_path and property names."

    except Exception as e:
        return format_error(e, "Use exact Unreal property names and a valid actor_or_mesh_path.")

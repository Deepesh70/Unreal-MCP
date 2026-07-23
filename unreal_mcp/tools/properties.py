"""
Property Tools — read and write ANY property on ANY actor or component.

These are generalized tools that replace the need for domain-specific setters
like set_light_intensity, set_camera_focal_length, set_material_roughness, etc.
One tool handles ALL of them.
"""

import json

from unreal_mcp import mcp
from unreal_mcp.connection import send_ue_ws_property, get_ue_ws_property
from unreal_mcp.utils import format_error


@mcp.tool()
async def set_actor_property(
    actor_path: str,
    property_name: str,
    property_value: str,
) -> str:
    """Set any property on any actor or component in Unreal Engine.

    This is a generalized property setter — instead of separate tools for
    light intensity, camera focal length, material roughness, etc., this
    single tool handles ALL of them.

    Args:
        actor_path: Full path to the actor (from get_scene_state or spawn_actor).
        property_name: The UE property name. Can be nested with dots for components.
                       Examples: "Intensity", "LightColor", "CurrentFocalLength",
                       "RelativeScale3D", "bHidden"
        property_value: JSON-encoded value. Examples:
                        "5000.0" for floats
                        '{"R":1,"G":0.8,"B":0.6,"A":1}' for colors
                        '{"X":1,"Y":2,"Z":3}' for vectors
                        "true" / "false" for booleans

    Returns:
        Confirmation of the property change.

    Examples:
        # Set light intensity
        set_actor_property("/Game/.../PointLight_1", "Intensity", "5000.0")

        # Set light color to warm orange
        set_actor_property("/Game/.../PointLight_1", "LightColor",
                          '{"R":1,"G":0.8,"B":0.6,"A":1}')
    """
    try:
        # Parse the value from JSON string to proper type
        try:
            parsed_value = json.loads(property_value)
        except (json.JSONDecodeError, TypeError):
            parsed_value = property_value  # Use as raw string if not valid JSON

        response = await send_ue_ws_property(
            object_path=actor_path,
            property_name=property_name,
            property_value=parsed_value,
        )

        short_name = actor_path.split(".")[-1]
        return f"Set {property_name} = {property_value} on {short_name}"

    except Exception as e:
        return format_error(e, "Check the property name and actor path.")


@mcp.tool()
async def get_actor_property(
    actor_path: str,
    property_name: str,
) -> str:
    """Read any property from any actor or component in Unreal Engine.

    Args:
        actor_path: Full path to the actor (from get_scene_state or spawn_actor).
        property_name: The UE property name to read.

    Returns:
        The current value of the property as a JSON string.
    """
    try:
        response = await get_ue_ws_property(
            object_path=actor_path,
            property_name=property_name,
        )

        # Extract the property value from response
        body = response.get("ResponseBody", {})
        prop_value = body.get(property_name, body)

        short_name = actor_path.split(".")[-1]
        return f"{property_name} on {short_name} = {json.dumps(prop_value)}"

    except Exception as e:
        return format_error(e, "Check the property name and actor path.")

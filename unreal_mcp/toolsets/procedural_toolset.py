"""
ProceduralCityToolset — Official Toolset Registry Plugin Definition (UE 5.8+).

This module conforms to Epic Games' Toolset Registry specification for Unreal Engine 5.8+.
When copied into a project's `Content/Python/toolset_registry/toolsets/` folder,
the official in-editor Unreal MCP server automatically exposes these functions as MCP tools.

It interfaces directly with `AProceduralCityManager` inside Unreal Engine.
"""

import json

try:
    import unreal
    import toolset_registry
    _IN_UNREAL = True
except ImportError:
    # Graceful fallback for non-UE environments (linting, tests, offline tools)
    _IN_UNREAL = False

    class _MockModule:
        def uclass(self):
            def decorator(cls):
                return cls
            return decorator

        def tool_call(self, func):
            return func

    unreal = _MockModule()
    toolset_registry = _MockModule()
    unreal.ToolsetDefinition = object


def _find_city_manager():
    """Find the AProceduralCityManager actor in the active editor world."""
    if not _IN_UNREAL:
        return None
    try:
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actors = subsystem.get_all_level_actors()
        for actor in actors:
            if "ProceduralCityManager" in actor.get_name() or "ProceduralCityManager" in actor.get_class().get_name():
                return actor
    except Exception:
        pass
    return None


@unreal.uclass()
class ProceduralCityToolset(unreal.ToolsetDefinition):
    """Provides tools for procedurally generating and managing 3D buildings,

    HISM structures, and city layouts via AProceduralCityManager.
    """

    @toolset_registry.tool_call
    @staticmethod
    def spawn_procedural_building(blueprint_json: str) -> str:
        """Spawn a procedural building or structure using the C++ Delegator engine.

        Args:
            blueprint_json: JSON string matching the Unreal-MCP Delegator blueprint schema.
                Must contain Intent ('Spawn'), ID, RequestedLoc ([x,y,z]), and Parameters.
        Returns:
            JSON receipt string indicating status, actual placed coordinates, and instance IDs.
        """
        if not _IN_UNREAL:
            return json.dumps({"Status": "Error", "Message": "Not running inside Unreal Engine Editor"})

        manager = _find_city_manager()
        if not manager:
            return json.dumps({
                "Status": "Error",
                "Message": "AProceduralCityManager actor not found in level. Please place one in the scene."
            })

        try:
            # ProcessBlueprint is exposed as a UFUNCTION on AProceduralCityManager
            receipt = manager.call_method("ProcessBlueprint", (blueprint_json,))
            return str(receipt)
        except Exception as e:
            return json.dumps({"Status": "Error", "Message": f"ProcessBlueprint failed: {str(e)}"})

    @toolset_registry.tool_call
    @staticmethod
    def batch_spawn_buildings(blueprints_json: str) -> str:
        """Spawn multiple buildings or district zones in a single coordinated operation.

        Args:
            blueprints_json: JSON string with Intent 'BatchSpawn' and an array of 'Blueprints'.
        Returns:
            JSON receipt string summarizing the batch generation results.
        """
        if not _IN_UNREAL:
            return json.dumps({"Status": "Error", "Message": "Not running inside Unreal Engine Editor"})

        manager = _find_city_manager()
        if not manager:
            return json.dumps({"Status": "Error", "Message": "AProceduralCityManager actor not found in level."})

        try:
            receipt = manager.call_method("ProcessBlueprint", (blueprints_json,))
            return str(receipt)
        except Exception as e:
            return json.dumps({"Status": "Error", "Message": f"Batch spawn failed: {str(e)}"})

    @toolset_registry.tool_call
    @staticmethod
    def clear_all_procedural() -> str:
        """Remove all procedural buildings and clear all HISM instances managed by CityManager.

        Returns:
            JSON receipt string confirming clearance.
        """
        if not _IN_UNREAL:
            return json.dumps({"Status": "Error", "Message": "Not running inside Unreal Engine Editor"})

        manager = _find_city_manager()
        if not manager:
            return json.dumps({"Status": "Error", "Message": "AProceduralCityManager actor not found in level."})

        payload = json.dumps({"Intent": "ClearAll"})
        try:
            receipt = manager.call_method("ProcessBlueprint", (payload,))
            return str(receipt)
        except Exception as e:
            return json.dumps({"Status": "Error", "Message": f"ClearAll failed: {str(e)}"})

    @toolset_registry.tool_call
    @staticmethod
    def destroy_procedural_building(building_id: str) -> str:
        """Remove a specific procedural building by its unique ID while keeping all other buildings intact.

        Args:
            building_id: The unique string identifier of the building to remove (e.g. 'House_01').
        Returns:
            JSON receipt string confirming deletion and ledger re-indexing.
        """
        if not _IN_UNREAL:
            return json.dumps({"Status": "Error", "Message": "Not running inside Unreal Engine Editor"})

        manager = _find_city_manager()
        if not manager:
            return json.dumps({"Status": "Error", "Message": "AProceduralCityManager actor not found in level."})

        payload = json.dumps({"Intent": "Destroy", "TargetID": building_id})
        try:
            receipt = manager.call_method("ProcessBlueprint", (payload,))
            return str(receipt)
        except Exception as e:
            return json.dumps({"Status": "Error", "Message": f"Destroy failed: {str(e)}"})

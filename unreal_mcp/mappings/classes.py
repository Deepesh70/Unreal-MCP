"""
Actor Class Mappings — Lights & Procedural Generators.

Maps friendly lowercase names to Unreal Engine class paths.
Add new actor types here; every tool that needs class lookups
imports from this single source of truth.
"""

# ── Class Map (Basic Engine Actors) ───────────────────────────────────
CLASS_MAP: dict[str, str] = {
    "pointlight":       "/Script/Engine.PointLight",
    "spotlight":        "/Script/Engine.SpotLight",
    "directional_light": "/Script/Engine.DirectionalLight",
}

# ── Generator Map (High-Performance C++ Procedural Classes) ───────────
# We isolate these so the LLM agent explicitly knows these are parametric 
# mathematical controllers, not just basic visual meshes.
# SUPPORTED_GENERATORS: dict[str, str] = {
#     "grid_generator": "/Script/Automator.GridGenerator"
# }

# ── Generator Map (High-Performance C++ Procedural Classes) ───────────
# We isolate these so the LLM agent explicitly knows these are parametric 
# mathematical controllers, not just basic visual meshes.
SUPPORTED_GENERATORS: dict[str, str] = {
    # Point to the Blueprint child, NOT the raw C++ script!
    "grid_generator": "/Game/BP_GridGenerator.BP_GridGenerator_C"
}

def get_class_path(name: str, fallback: str | None = None) -> str:
    """
    Look up an actor class path by friendly name (case-insensitive).
    Checks the procedural generators first, then the basic engine classes.
    """
    if fallback is None:
        fallback = name
        
    lower_name = name.lower()
    
    # Check if it is a high-performance generator first
    if lower_name in SUPPORTED_GENERATORS:
        return SUPPORTED_GENERATORS[lower_name]
        
    # Fallback to basic lights/engine classes
    return CLASS_MAP.get(lower_name, fallback)


def get_available_generators() -> list[str]:
    """
    Returns a list of high-performance procedural generators the AI can use.
    Inject this into your system prompt or list_supported_types tool.
    """
    return list(SUPPORTED_GENERATORS.keys())
"""
=== UNREAL MCP CODE GENERATION DEMO ===
Run:  python demo_codegen.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from unreal_mcp.codegen import Blueprint, Variable, Function, render_header, render_source

print("=" * 65)
print("  UNREAL MCP - Structured Code Generation Demo")
print("  LLM outputs JSON -> Server generates proper UE C++")
print("=" * 65)

# === This is what the LLM would output (just JSON, no C++) ===
blueprint = Blueprint(
    class_name="AntiGravity",
    parent_class="AActor",
    description="Negates gravity for any actor inside its radius",
    variables=[
        Variable(name="GravityScale", type="float", default="-980.0f",
                 category="Physics", tooltip="Strength of anti-gravity force"),
        Variable(name="EffectRadius", type="float", default="500.0f",
                 category="Physics", tooltip="Radius of the effect zone"),
        Variable(name="ForceDirection", type="vector",
                 category="Physics"),
        Variable(name="IsActive", type="bool", default="true",
                 category="State"),
        Variable(name="EffectColor", type="color",
                 category="Visuals"),
    ],
    functions=[
        Function(name="ToggleAntiGravity",
                 body="IsActive = !IsActive;",
                 description="Toggle the effect on/off"),
        Function(name="GetEffectStrength", return_type="float",
                 body="return GravityScale * (IsActive ? 1.0f : 0.0f);",
                 description="Returns current force magnitude"),
    ],
    tick_enabled=True,
    tick_body="if (IsActive)\n\t{\n\t\t// Apply anti-gravity to overlapping actors\n\t}",
    begin_play_body="UE_LOG(LogTemp, Log, TEXT(\"AntiGravity Zone Activated\"));",
)

print("\n--- LLM JSON Input (what the AI outputs) ---")
print(blueprint.model_dump_json(indent=2))

header = render_header(blueprint)
source = render_source(blueprint)

print("\n\n--- Generated: AntiGravity.h ---")
print(header)

print("\n--- Generated: AntiGravity.cpp ---")
print(source)

print("=" * 65)
print(f"  Header: {len(header)} bytes  |  Source: {len(source)} bytes")
print(f"  Variables: {len(blueprint.variables)}  |  Functions: {len(blueprint.functions)}")
print(f"  Tick: {'ENABLED' if blueprint.tick_enabled else 'disabled'}")
print(f"  Zero hallucinations. Zero boilerplate from the LLM.")
print("=" * 65)

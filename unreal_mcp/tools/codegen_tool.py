"""
Code Generation Tool — generate_ue_class MCP tool.

The LLM calls this tool with a structured JSON Blueprint,
and the server renders it into proper .h/.cpp files.
"""

import json
from unreal_mcp import mcp
from unreal_mcp.codegen.schema import UnrealClassSchema
from unreal_mcp.codegen.renderer import render_both
from unreal_mcp.codegen.file_writer import write_class_files
from unreal_mcp.utils import format_error


@mcp.tool()
async def generate_ue_class(blueprint_json: str) -> str:
    """Generate a UE C++ class from structured JSON. Pass a JSON object with: class_name (string), parent_class (string, default AActor), variables (array of {name, type, default, category}), functions (array of {name, return_type, params, body}), tick_enabled (bool), tick_body (string), begin_play_body (string)."""
    try:
        # Parse and validate the JSON
        data = json.loads(blueprint_json)
        schema = UnrealClassSchema(**data)

        # Render C++ code from templates
        header_code, source_code = render_both(schema)

        # Write to UE project
        try:
            header_path, source_path = write_class_files(
                class_name=schema.class_name,
                header_code=header_code,
                source_code=source_code,
            )
            file_msg = f"\nFiles written:\n  .h: {header_path}\n  .cpp: {source_path}"
        except Exception as write_err:
            file_msg = f"\nCould not write files: {write_err}\nCode generated in memory only."

        # Build summary
        var_count = len(schema.variables)
        func_count = len(schema.methods)
        prefix = "A" if schema.parent_class.startswith("A") else "U"

        summary = (
            f"Generated {prefix}{schema.class_name} : {schema.parent_class}\n"
            f"  Variables: {var_count}\n"
            f"  Methods: {func_count}\n"
            f"{file_msg}"
            f"\n\n--- HEADER ---\n{header_code}"
            f"\n\n--- SOURCE ---\n{source_code}"
        )
        return summary

    except json.JSONDecodeError as e:
        return format_error(e, "Invalid JSON — make sure to output valid JSON.")
    except Exception as e:
        return format_error(e, "Check the Blueprint JSON structure.")


@mcp.tool()
async def preview_ue_class(blueprint_json: str) -> str:
    """Preview generated C++ code WITHOUT writing files. Same JSON format as generate_ue_class."""
    try:
        data = json.loads(blueprint_json)
        schema = UnrealClassSchema(**data)
        header_code, source_code = render_both(schema)

        prefix = "A" if schema.parent_class.startswith("A") else "U"
        return (
            f"Preview of {prefix}{schema.class_name}:\n\n"
            f"--- {schema.class_name}.h ---\n{header_code}\n\n"
            f"--- {schema.class_name}.cpp ---\n{source_code}"
        )

    except json.JSONDecodeError as e:
        return format_error(e, "Invalid JSON.")
    except Exception as e:
        return format_error(e, "Check the Blueprint JSON structure.")

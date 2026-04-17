"""
Template Renderer — Renders Blueprint schemas into C++ code.
Bypasses Jinja2 templates entirely for strict schema formatting.
"""

from __future__ import annotations
import re
from unreal_mcp.codegen.schema import UnrealClassSchema
from unreal_mcp.config.settings import UE_PROJECT_NAME

def _build_project_api(project_name: str) -> str:
    """Build the PROJECT_API macro, e.g. MYPROJECT_API."""
    return f"{project_name.upper()}_API"

def render_header(schema: UnrealClassSchema) -> str:
    """Render the .h header file for an UnrealClassSchema using strict string formatting."""
    api_macro = _build_project_api(UE_PROJECT_NAME)
    prefix = "A" if schema.parent_class.startswith("A") else "U"
    ue_class_name = f"{prefix}{schema.class_name}"
    
    lines = []
    lines.append("#pragma once")
    lines.append("")
    lines.append('#include "CoreMinimal.h"')
    
    for inc in schema.includes:
        inc = inc.strip()
        if not inc or ".generated.h" in inc:
            continue
        if inc.startswith("#include"):
            lines.append(inc)
        else:
            lines.append(f'#include "{inc}"')
            
    lines.append(f'#include "{schema.class_name}.generated.h"')
    lines.append("")
    lines.append("UCLASS()")
    lines.append(f"class {api_macro} {ue_class_name} : public {schema.parent_class}")
    lines.append("{")
    lines.append("\tGENERATED_BODY()")
    lines.append("")
    lines.append("public:")
    lines.append(f"\t{ue_class_name}();")
    lines.append("")
    is_actor = schema.parent_class.startswith("A")
    
    lines.append("protected:")
    lines.append("\tvirtual void BeginPlay() override;")
    lines.append("")
    lines.append("public:")
    if is_actor:
        lines.append("\tvirtual void Tick(float DeltaTime) override;")
    else:
        lines.append("\tvirtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;")
    lines.append("")
    
    # Variables
    for var in schema.variables:
        lines.append('\tUPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Default")')
        lines.append(f"\t{var.type} {var.name};")
        lines.append("")
        
    # Methods (extract signatures from implementations)
    for method in schema.methods:
        method = method.strip()
        # Find everything before the first opening brace as the signature
        idx = method.find("{")
        if idx != -1:
            sig = method[:idx].strip()
            if not sig.endswith(";"):
                sig += ";"
        else:
            sig = method if method.endswith(";") else method + ";"
        # For methods, remove trailing semicolon to make signature clean
        if sig.endswith(";"):
            sig = sig[:-1]
            
        lines.append(f"\tUFUNCTION(BlueprintCallable, Category = \"Default\")")
        lines.append(f"\t{sig};")
        lines.append("")

    lines.append("};")
    return "\n".join(lines)


def render_source(schema: UnrealClassSchema) -> str:
    """Render the .cpp source file for an UnrealClassSchema."""
    prefix = "A" if schema.parent_class.startswith("A") else "U"
    ue_class_name = f"{prefix}{schema.class_name}"
    
    lines = []
    lines.append(f'#include "{schema.class_name}.h"')
    lines.append("")
    
    lines.append(f"{ue_class_name}::{ue_class_name}()")
    lines.append("{")
    is_actor = schema.parent_class.startswith("A")
    if is_actor:
        lines.append("\tPrimaryActorTick.bCanEverTick = true;")
    else:
        lines.append("\tPrimaryComponentTick.bCanEverTick = true;")
    lines.append("")
    for var in schema.variables:
        if var.default_value:
            lines.append(f"\t{var.name} = {var.default_value};")
            
    if schema.constructor_body:
        # Indent constructor body
        body_lines = schema.constructor_body.strip().split("\n")
        for bl in body_lines:
            lines.append(f"\t{bl}")
            
    lines.append("}")
    lines.append("")
    
    lines.append(f"void {ue_class_name}::BeginPlay()")
    lines.append("{")
    lines.append("\tSuper::BeginPlay();")
    lines.append("}")
    lines.append("")
    
    if is_actor:
        lines.append(f"void {ue_class_name}::Tick(float DeltaTime)")
        lines.append("{")
        lines.append("\tSuper::Tick(DeltaTime);")
        lines.append("}")
    else:
        lines.append(f"void {ue_class_name}::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)")
        lines.append("{")
        lines.append("\tSuper::TickComponent(DeltaTime, TickType, ThisTickFunction);")
        lines.append("}")
    lines.append("")
    
    for method in schema.methods:
        method = method.strip()
        # If the method string ends with a semicolon, it's just a signature. We must give it an empty body.
        has_body = "{" in method
        
        match = re.match(r'^([\w\s\*&<>]+)\s+(\w+)\s*\(', method)
        if match:
            ret_type = match.group(1).strip()
            name = match.group(2).strip()
            # Replace the signature to include ClassName::
            impl = method.replace(f"{ret_type} {name}(", f"{ret_type} {ue_class_name}::{name}(", 1)
            
            if not has_body:
                if impl.endswith(";"):
                    impl = impl[:-1]
                impl += "\n{\n}\n"
            
            lines.append(impl)
        else:
            # Fallback
            if not has_body:
                if method.endswith(";"):
                    method = method[:-1]
                method += "\n{\n}\n"
            lines.append(method)
            
        lines.append("")
        
    return "\n".join(lines)


def render_both(schema: UnrealClassSchema) -> tuple[str, str]:
    """Render both .h and .cpp files. Returns (header_code, source_code)."""
    return render_header(schema), render_source(schema)

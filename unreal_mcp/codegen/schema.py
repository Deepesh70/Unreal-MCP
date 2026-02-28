"""
Blueprint Schema — Pydantic models defining the structured JSON
the LLM must output.

The LLM never writes raw C++. It outputs a Blueprint JSON that
the server renders through Jinja2 templates into proper UE code.
"""

from __future__ import annotations
from pydantic import BaseModel, Field


class Variable(BaseModel):
    """A single UPROPERTY variable in the generated class."""

    name: str = Field(description="PascalCase variable name, e.g. WindSpeed")
    type: str = Field(description="Friendly type: float, int, bool, string, vector, rotator, color, actor_ref, mesh")
    default: str = Field(default="", description="Default value as a string, e.g. '10.0f'")
    category: str = Field(default="Default", description="Editor category for UPROPERTY grouping")
    editable: bool = Field(default=True, description="If true, EditAnywhere in Editor")
    tooltip: str = Field(default="", description="Tooltip shown in Editor")


class FunctionParam(BaseModel):
    """A parameter for a generated UFUNCTION."""

    name: str = Field(description="Parameter name")
    type: str = Field(description="Friendly type")


class Function(BaseModel):
    """A single UFUNCTION in the generated class."""

    name: str = Field(description="PascalCase function name, e.g. UpdateWeather")
    return_type: str = Field(default="void", description="Return type (friendly)")
    params: list[FunctionParam] = Field(default_factory=list)
    body: str = Field(default="", description="Pure C++ logic — no boilerplate, just the implementation")
    callable: bool = Field(default=True, description="If true, BlueprintCallable")
    description: str = Field(default="", description="Brief function description")


class Blueprint(BaseModel):
    """
    Complete class blueprint that the LLM outputs.
    The server renders this into .h + .cpp files.
    """

    class_name: str = Field(description="PascalCase class name without A/U prefix, e.g. DynamicWeather")
    parent_class: str = Field(default="AActor", description="AActor, UActorComponent, APawn, ACharacter, etc.")
    description: str = Field(default="", description="One-line class description")
    variables: list[Variable] = Field(default_factory=list)
    functions: list[Function] = Field(default_factory=list)
    tick_enabled: bool = Field(default=False, description="Whether to enable Tick")
    tick_body: str = Field(default="", description="C++ logic for Tick(), if enabled")
    begin_play_body: str = Field(default="", description="C++ logic for BeginPlay()")
    constructor_body: str = Field(default="", description="Extra C++ logic for the constructor")
    extra_includes: list[str] = Field(default_factory=list, description="Additional #include paths if needed")

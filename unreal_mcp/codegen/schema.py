from pydantic import BaseModel, Field, field_validator
from typing import List, Literal

class UnrealVariable(BaseModel):
    type: str = Field(description="The C++ type, e.g., FVector, float, bool")
    name: str = Field(description="Variable name, starting with a capital letter.")
    default_value: str = Field(default="", description="Valid C++ default value.")

    @field_validator('default_value')
    @classmethod
    def validate_no_json_garbage(cls, v):
        if "{" in v or ":" in v:
            raise ValueError(f"Garbage syntax detected: {v}. Use proper C++.")
        return v

class ProceduralComponent(BaseModel):
    name: str = Field(description="Name of the component. MUST be a valid C++ variable name without spaces (e.g., NorthWall).")
    shape: Literal["Cube", "Sphere", "Cylinder", "Cone", "Plane"] = Field(description="The primitive shape to use.")
    location: str = Field(default="FVector::ZeroVector", description="C++ FVector for relative location.")
    rotation: str = Field(default="FRotator::ZeroRotator", description="C++ FRotator for relative rotation.")
    scale: str = Field(default="FVector(1.0f, 1.0f, 1.0f)", description="C++ FVector for 3D scale.")

    @field_validator('name')
    @classmethod
    def validate_c_identifier(cls, v):
        if not v.isalnum():
            raise ValueError(f"Component name '{v}' must be alphanumeric with no spaces.")
        return v

class UnrealClassSchema(BaseModel):
    class_name: str = Field(description="Exact class name WITHOUT the A or U prefix.")
    parent_class: str = Field(description="Typically AActor")
    includes: List[str]
    variables: List[UnrealVariable]
    procedural_components: List[ProceduralComponent] = Field(
        min_length=1, 
        description="List of 3D physical shapes to assemble. YOU MUST PROVIDE AT LEAST ONE COMPONENT. DO NOT LEAVE THIS EMPTY."
    )
    constructor_body: str = Field(default="", description="C++ logic for the constructor")
    methods: List[str] = Field(default_factory=list, description="List of full C++ method implementations")

    @field_validator('class_name')
    @classmethod
    def validate_prefix(cls, v):
        if v.startswith('A') or v.startswith('U'):
            if len(v) > 1 and v[1].isupper():
                raise ValueError("Do not include the A or U prefix in class_name.")
        return v

    @field_validator('includes')
    @classmethod
    def validate_banned_includes(cls, v):
        for inc in v:
            if "ProceduralMeshComponent" in inc:
                raise ValueError("CRITICAL FAILURE: You included ProceduralMeshComponent.h. You are strictly forbidden from using ProceduralMesh components. Use StaticMeshComponent instead. Regenerate the schema.")
        return v

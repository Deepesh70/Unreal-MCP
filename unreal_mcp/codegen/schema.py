from pydantic import BaseModel, Field, field_validator

class UnrealVariable(BaseModel):
    name: str = Field(description="Variable name")
    type: str = Field(description="C++ Type")
    default_value: str = Field(default="", description="Default value as string")

    @field_validator("default_value")
    @classmethod
    def validate_no_json(cls, v: str) -> str:
        if "{" in v or ":" in v:
            raise ValueError(f"JSON syntax detected in default_value: {v}. Must be valid C++ syntax.")
        return v

class UnrealClassSchema(BaseModel):
    class_name: str = Field(description="PascalCase class name without A/U prefix")
    parent_class: str = Field(description="Parent class name (e.g. AActor, UActorComponent)")
    includes: list[str] = Field(description="List of #includes as strings")
    variables: list[UnrealVariable] = Field(description="List of variables")
    constructor_body: str = Field(default="", description="C++ logic for the constructor")
    methods: list[str] = Field(default_factory=list, description="List of full C++ method implementations (e.g. 'void Fire() { ... }')")

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, v: str) -> str:
        if v.startswith("A") or v.startswith("U"):
            if len(v) > 1 and v[1].isupper():
                raise ValueError(f"class_name '{v}' must NOT include the 'A' or 'U' prefix.")
        return v

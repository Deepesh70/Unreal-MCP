"""
Type Mapper — Maps friendly type names to Unreal Engine C++ types.

The LLM outputs simple types like "float", "vector", "color" and this
module resolves them to proper UE types with correct includes.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class UEType:
    """A resolved Unreal Engine type."""
    cpp_type: str
    include: str | None = None
    default: str = ""


# ── Master Type Map ──────────────────────────────────────────────────
TYPE_MAP: dict[str, UEType] = {
    # Primitives
    "float":      UEType(cpp_type="float",            default="0.0f"),
    "double":     UEType(cpp_type="double",           default="0.0"),
    "int":        UEType(cpp_type="int32",            default="0"),
    "int32":      UEType(cpp_type="int32",            default="0"),
    "int64":      UEType(cpp_type="int64",            default="0"),
    "bool":       UEType(cpp_type="bool",             default="false"),
    "byte":       UEType(cpp_type="uint8",            default="0"),

    # Strings
    "string":     UEType(cpp_type="FString",          default="TEXT(\"\")"),
    "name":       UEType(cpp_type="FName",            default="NAME_None"),
    "text":       UEType(cpp_type="FText",            default="FText::GetEmpty()"),

    # Math
    "vector":     UEType(cpp_type="FVector",          default="FVector::ZeroVector",
                         include="Math/Vector.h"),
    "vector2d":   UEType(cpp_type="FVector2D",        default="FVector2D::ZeroVector",
                         include="Math/Vector2D.h"),
    "rotator":    UEType(cpp_type="FRotator",         default="FRotator::ZeroRotator",
                         include="Math/Rotator.h"),
    "transform":  UEType(cpp_type="FTransform",       default="FTransform::Identity",
                         include="Math/Transform.h"),
    "color":      UEType(cpp_type="FLinearColor",     default="FLinearColor::White",
                         include="Math/Color.h"),
    "quat":       UEType(cpp_type="FQuat",            default="FQuat::Identity",
                         include="Math/Quat.h"),

    # Object References
    "actor_ref":  UEType(cpp_type="AActor*",          default="nullptr",
                         include="GameFramework/Actor.h"),
    "class_ref":  UEType(cpp_type="UClass*",          default="nullptr"),
    "object_ref": UEType(cpp_type="UObject*",         default="nullptr"),

    # Components
    "mesh":       UEType(cpp_type="UStaticMeshComponent*",   default="nullptr",
                         include="Components/StaticMeshComponent.h"),
    "skeletal":   UEType(cpp_type="USkeletalMeshComponent*", default="nullptr",
                         include="Components/SkeletalMeshComponent.h"),
    "scene":      UEType(cpp_type="USceneComponent*",        default="nullptr",
                         include="Components/SceneComponent.h"),
    "audio":      UEType(cpp_type="UAudioComponent*",        default="nullptr",
                         include="Components/AudioComponent.h"),
    "particle":   UEType(cpp_type="UParticleSystemComponent*", default="nullptr",
                         include="Particles/ParticleSystemComponent.h"),
    "light":      UEType(cpp_type="UPointLightComponent*",   default="nullptr",
                         include="Components/PointLightComponent.h"),
    "collision":  UEType(cpp_type="USphereComponent*",       default="nullptr",
                         include="Components/SphereComponent.h"),
    "capsule":    UEType(cpp_type="UCapsuleComponent*",      default="nullptr",
                         include="Components/CapsuleComponent.h"),
    "box":        UEType(cpp_type="UBoxComponent*",          default="nullptr",
                         include="Components/BoxComponent.h"),

    # Gameplay
    "timer":      UEType(cpp_type="FTimerHandle",     default=""),
    "curve":      UEType(cpp_type="UCurveFloat*",     default="nullptr",
                         include="Curves/CurveFloat.h"),
    "material":   UEType(cpp_type="UMaterialInterface*", default="nullptr",
                         include="Materials/MaterialInterface.h"),

    # Special
    "void":       UEType(cpp_type="void"),
}


def resolve_type(friendly_name: str) -> UEType:
    """
    Resolve a friendly type name to a UEType.

    If the name isn't in the map, treat it as a raw C++ type
    (allows the LLM to pass through custom types).
    """
    return TYPE_MAP.get(friendly_name.lower(), UEType(cpp_type=friendly_name))


def get_required_includes(friendly_types: list[str]) -> list[str]:
    """Collect all #include paths needed for a list of friendly types."""
    includes = set()
    for t in friendly_types:
        ue_type = resolve_type(t)
        if ue_type.include:
            includes.add(ue_type.include)
    return sorted(includes)

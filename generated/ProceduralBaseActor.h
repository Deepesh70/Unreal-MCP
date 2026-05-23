// ProceduralBaseActor.h
// Persistent base class providing HISM bulk-instantiation capabilities
// to all LLM-generated procedural actors.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "ProceduralBuildingTypes.h"
#include "ProceduralBaseActor.generated.h"

UCLASS()
class {{PROJECT_API}} AProceduralBaseActor : public AActor
{
    GENERATED_BODY()
    
public: 
    AProceduralBaseActor();

    // The HISM Pool: maps a mesh/material pair to a specific HISM component
    UPROPERTY(VisibleAnywhere, Category="Procedural")
    TMap<FHISMPoolKey, TObjectPtr<UHierarchicalInstancedStaticMeshComponent>> HISMPool;

    // Retrieve an existing HISM for the mesh/material, or create a new one
    UFUNCTION(BlueprintCallable, Category="Procedural")
    UHierarchicalInstancedStaticMeshComponent* GetOrCreateHISM(UStaticMesh* Mesh, UMaterialInterface* Material = nullptr);

    // Parses a JSON array of transforms and bulk-spawns them using the provided asset
    UFUNCTION(BlueprintCallable, Category="Procedural")
    bool HandleInstancedSpawn(const FString& AssetPath, const FString& TransformsJson);
};

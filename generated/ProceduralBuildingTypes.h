// ProceduralBuildingTypes.h — Data structures for the Procedural City Builder.
//
// This file contains all UStructs used by AProceduralCityManager:
//   - FHISMPoolKey        : Composite key for the HISM component pool
//   - FHISMInstanceRef    : Tracks one HISM instance (component + index)
//   - FProceduralBuilding : Ledger entry — one per building
//   - FAssetDictionaryRow : DataTable row mapping Style tags to meshes/materials
//
// SETUP: Copy this file to your Unreal project's Source/ directory.
//        Replace {{PROJECT_API}} with your project's API export macro.
//        Add "Json", "JsonUtilities" to your Build.cs PublicDependencyModuleNames.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "ProceduralBuildingTypes.generated.h"


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  FHISMPoolKey — Composite key for the HISM component pool.
//  One HISM component per unique {Mesh, Material} pair.
//  This ensures different material styles on the same mesh get
//  separate HISM components (e.g., wood walls vs concrete walls).
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USTRUCT()
struct FHISMPoolKey
{
	GENERATED_BODY()

	UPROPERTY()
	TObjectPtr<UStaticMesh> Mesh = nullptr;

	UPROPERTY()
	TObjectPtr<UMaterialInterface> Material = nullptr;

	bool operator==(const FHISMPoolKey& Other) const
	{
		return Mesh == Other.Mesh && Material == Other.Material;
	}

	friend uint32 GetTypeHash(const FHISMPoolKey& Key)
	{
		return HashCombine(GetTypeHash(Key.Mesh), GetTypeHash(Key.Material));
	}
};


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  FHISMInstanceRef — Tracks a single HISM instance.
//  Stored per-building so we know exactly which instances to remove
//  during Modify/Destroy operations.
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USTRUCT()
struct FHISMInstanceRef
{
	GENERATED_BODY()

	UPROPERTY()
	TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Component = nullptr;

	UPROPERTY()
	int32 InstanceIndex = -1;
};


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  FProceduralBuilding — Ledger entry. One per spawned building.
//  The Ledger (TMap<FString, FProceduralBuilding>) is the single
//  source of truth for what exists in the procedural world.
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USTRUCT()
struct FProceduralBuilding
{
	GENERATED_BODY()

	UPROPERTY()
	FString BuildingID;

	UPROPERTY()
	FString StyleKey;

	UPROPERTY()
	FVector Location = FVector::ZeroVector;

	UPROPERTY()
	TArray<FHISMInstanceRef> Instances;
};


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  FAssetDictionaryRow — DataTable row for the Asset Dictionary.
//  Maps a semantic Style tag (row name) to actual meshes and materials.
//  If the DataTable is missing or a style isn't found, the system
//  falls back to /Engine/BasicShapes/Cube and /Engine/BasicShapes/Cone.
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USTRUCT(BlueprintType)
struct FAssetDictionaryRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Meshes")
	TSoftObjectPtr<UStaticMesh> WallMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Meshes")
	TSoftObjectPtr<UStaticMesh> FloorMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Meshes")
	TSoftObjectPtr<UStaticMesh> RoofMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Materials")
	TSoftObjectPtr<UMaterialInterface> WallMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Materials")
	TSoftObjectPtr<UMaterialInterface> FloorMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Materials")
	TSoftObjectPtr<UMaterialInterface> RoofMaterial;
};

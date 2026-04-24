// ProceduralCityManager.h — The master builder actor.
//
// Place ONE of these in your Unreal level. Python discovers it at runtime
// via list_actors and calls ProcessBlueprint() over the Remote Control API.
//
// SETUP: Copy to your project's Source/ directory alongside ProceduralBuildingTypes.h.
//        Replace {{PROJECT_API}} with your project's API export macro.
//        Add "Json", "JsonUtilities" to your Build.cs PublicDependencyModuleNames.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ProceduralBuildingTypes.h"

// Geometry Scripting — runtime boolean operations and dynamic mesh generation
#include "GeometryScript/MeshPrimitiveFunctions.h"
#include "GeometryScript/MeshBooleanFunctions.h"
#include "Components/DynamicMeshComponent.h"
#include "DynamicMeshActor.h"
#include "UDynamicMesh.h"

#include "ProceduralCityManager.generated.h"

class UDataTable;
class UHierarchicalInstancedStaticMeshComponent;
class UDynamicMeshComponent;

UCLASS(Blueprintable, Placeable, meta = (DisplayName = "Procedural City Manager"))
class {{PROJECT_API}} AProceduralCityManager : public AActor
{
	GENERATED_BODY()

public:
	AProceduralCityManager();

	// ── Main Entry Point ─────────────────────────────────────────
	// Called by Python via the WebSocket Remote Control API.
	// Accepts a JSON string, routes by Intent, returns a JSON receipt.
	UFUNCTION(BlueprintCallable, Category = "Procedural")
	FString ProcessBlueprint(const FString& JsonPayload);

	// ── Debug / Editor Helpers ───────────────────────────────────
	UFUNCTION(BlueprintCallable, Category = "Procedural")
	int32 GetBuildingCount() const { return Ledger.Num(); }

	UFUNCTION(BlueprintCallable, Category = "Procedural")
	TArray<FString> GetBuildingIDs() const;

protected:
	// ── Assets ──────────────────────────────────────────────────
	// Optional DataTable mapping Style tags → meshes/materials.
	// If null or if a style isn't found, falls back to basic shapes.
	UPROPERTY(EditDefaultsOnly, Category = "Assets")
	TObjectPtr<UDataTable> AssetDictionary;

	// Fallback meshes loaded in constructor
	UPROPERTY()
	TObjectPtr<UStaticMesh> DefaultCubeMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> DefaultConeMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> DefaultSphereMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> DefaultCylinderMesh;

	// ── State ───────────────────────────────────────────────────
	// The Ledger — single source of truth for all procedural buildings.
	UPROPERTY(VisibleAnywhere, Category = "State")
	TMap<FString, FProceduralBuilding> Ledger;

	// Pool of HISM components — one per unique {Mesh, Material} pair.
	UPROPERTY()
	TMap<FHISMPoolKey, TObjectPtr<UHierarchicalInstancedStaticMeshComponent>> HISMPool;

private:
	// ── Intent Handlers ─────────────────────────────────────────
	FString HandleSpawn(TSharedPtr<FJsonObject> Json);
	FString HandleBatchSpawn(TSharedPtr<FJsonObject> Json);
	FString HandleModify(TSharedPtr<FJsonObject> Json);
	FString HandleDestroy(TSharedPtr<FJsonObject> Json);
	FString HandleClearAll();
	FString HandleScanArea(TSharedPtr<FJsonObject> Json);
	FString HandleGenerateGeometry(TSharedPtr<FJsonObject> Json);

	// ── Core Building Logic ─────────────────────────────────────
	// Routes by StructureType: Building, Solid, Composite
	bool SpawnBuildingGeometry(const FString& ID, const FString& StyleKey,
		FVector Location, TSharedPtr<FJsonObject> Params,
		TSharedPtr<FJsonObject> FullJson = nullptr);

	// Solid: spawn a single scaled primitive
	bool SpawnSolidGeometry(const FString& ID, FVector Location,
		TSharedPtr<FJsonObject> Params);

	// Composite: spawn multiple primitives from a Parts array
	bool SpawnCompositeGeometry(const FString& ID, FVector Location,
		TSharedPtr<FJsonObject> Params, const TArray<TSharedPtr<FJsonValue>>& Parts);

	// DestroyBuilding: Swap-and-Pop safe removal of all HISM instances
	// belonging to a building, then removes it from the Ledger.
	void DestroyBuilding(const FString& ID);

	// After RemoveInstance, the last array element is swapped into the
	// vacated slot. This function finds whichever building owns that
	// swapped element and updates its tracked index.
	void SwapAndPopReindex(UHierarchicalInstancedStaticMeshComponent* Component,
		int32 RemovedIndex, int32 OldLastIndex);

	// ── HISM Pool Management ────────────────────────────────────
	UHierarchicalInstancedStaticMeshComponent* GetOrCreateHISM(
		UStaticMesh* Mesh, UMaterialInterface* Material = nullptr);

	// ── Geometry Scripting Helpers ───────────────────────────────
	// Appends a primitive shape onto a UDynamicMesh at the given transform.
	void AppendPrimitiveToMesh(UDynamicMesh* TargetMesh,
		const FString& ShapeType, FVector Dimensions,
		FTransform Transform);

	// Applies a material to a DynamicMeshComponent by color name.
	void ApplyMaterialByColor(UDynamicMeshComponent* MeshComp,
		const FString& ColorName);

	// Pool of DynamicMesh components — one per GenerateGeometry ID.
	UPROPERTY()
	TMap<FString, TObjectPtr<UDynamicMeshComponent>> DynamicMeshPool;

	// ── Mesh Resolution ─────────────────────────────────────────
	UStaticMesh* GetMeshForShape(const FString& ShapeName);

	// ── Asset Resolution ────────────────────────────────────────
	void ResolveMeshes(const FString& StyleKey,
		UStaticMesh*& OutWallMesh, UStaticMesh*& OutFloorMesh,
		UStaticMesh*& OutRoofMesh, UMaterialInterface*& OutWallMat,
		UMaterialInterface*& OutFloorMat, UMaterialInterface*& OutRoofMat);

	// ── Spatial Awareness (Dual-Check) ──────────────────────────
	// FindClearLocation: spirals outward from Requested, checking both
	// external (physics) and internal (Ledger) obstacles.
	FVector FindClearLocation(FVector Requested, float Radius,
		FVector BuildingExtents, bool& bOutFound);

	// External check: BoxOverlapActors for terrain, BSP, placed meshes.
	bool IsExternallyClear(FVector Point, FVector Extents);

	// Internal check: FVector::Dist against all Ledger entries. No physics.
	bool IsInternallyClear(FVector Point, float MinDistance);

	// Line trace downward to find the ground surface Z at a location.
	float GetGroundZ(FVector Location);

	// ── JSON Receipt Builders ───────────────────────────────────
	// All receipts use FJsonSerializer for proper escaping (no string concat).
	FString BuildReceipt(const FString& Action, const FString& Status,
		const FString& ID, FVector RequestedLoc, FVector ActualLoc,
		const FString& Reason = TEXT(""));

	FString BuildScanReceipt(float GroundZ,
		const TArray<FString>& ExternalCollisions,
		const TArray<FString>& InternalCollisions);

	// ── Utility ─────────────────────────────────────────────────
	// Finds which building in the Ledger owns a specific HISM instance index.
	FProceduralBuilding* FindBuildingOwningIndex(
		UHierarchicalInstancedStaticMeshComponent* Component, int32 Index);

	// Converts a JSON array [X, Y, Z] to an FVector.
	static FVector JsonArrayToVector(const TArray<TSharedPtr<FJsonValue>>& Arr);

	// Serializes an FVector to a JSON array [X, Y, Z].
	static TArray<TSharedPtr<FJsonValue>> VectorToJsonArray(FVector Vec);
};

// ProceduralCityManager.cpp — Full implementation of the Procedural City Builder.
//
// All 3 phases implemented:
//   Phase 1: Spawn, ClearAll, math loop, HISM pool, Ledger
//   Phase 2: ScanArea (Dual-Check), auto-nudge spiral, GroundZ trace
//   Phase 3: BatchSpawn, Modify, Destroy, Swap-and-Pop safe deletion,
//            DataTable asset resolution

#include "ProceduralCityManager.h"

#include "Engine/StaticMesh.h"
#include "Engine/DataTable.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Kismet/KismetSystemLibrary.h"

// JSON
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonWriter.h"
#include "Serialization/JsonSerializer.h"


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  Constructor
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AProceduralCityManager::AProceduralCityManager()
{
	PrimaryActorTick.bCanEverTick = false;

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("RootComponent"));
	SetRootComponent(Root);

	// Load fallback meshes from engine content.
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(
		TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeFinder.Succeeded())
	{
		DefaultCubeMesh = CubeFinder.Object;
	}

	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeFinder(
		TEXT("/Engine/BasicShapes/Cone.Cone"));
	if (ConeFinder.Succeeded())
	{
		DefaultConeMesh = ConeFinder.Object;
	}

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereFinder(
		TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereFinder.Succeeded())
	{
		DefaultSphereMesh = SphereFinder.Object;
	}

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(
		TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (CylinderFinder.Succeeded())
	{
		DefaultCylinderMesh = CylinderFinder.Object;
	}
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  Debug Helpers
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TArray<FString> AProceduralCityManager::GetBuildingIDs() const
{
	TArray<FString> IDs;
	Ledger.GetKeys(IDs);
	return IDs;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ProcessBlueprint — The single entry point called via Remote Control.
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FString AProceduralCityManager::ProcessBlueprint(const FString& JsonPayload)
{
	// Parse the incoming JSON string
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonPayload);
	TSharedPtr<FJsonObject> JsonObj;

	if (!FJsonSerializer::Deserialize(Reader, JsonObj) || !JsonObj.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("ProceduralCityManager: Failed to parse JSON payload."));
		return BuildReceipt(TEXT("BuildResult"), TEXT("Failed"), TEXT(""),
			FVector::ZeroVector, FVector::ZeroVector,
			TEXT("Failed to parse JSON payload"));
	}

	// Route by Intent
	FString Intent;
	if (!JsonObj->TryGetStringField(TEXT("Intent"), Intent))
	{
		UE_LOG(LogTemp, Error, TEXT("ProceduralCityManager: JSON missing 'Intent' field."));
		return BuildReceipt(TEXT("BuildResult"), TEXT("Failed"), TEXT(""),
			FVector::ZeroVector, FVector::ZeroVector,
			TEXT("JSON payload missing 'Intent' field"));
	}

	if (Intent == TEXT("Spawn"))      return HandleSpawn(JsonObj);
	if (Intent == TEXT("BatchSpawn")) return HandleBatchSpawn(JsonObj);
	if (Intent == TEXT("Modify"))     return HandleModify(JsonObj);
	if (Intent == TEXT("Destroy"))    return HandleDestroy(JsonObj);
	if (Intent == TEXT("ClearAll"))   return HandleClearAll();
	if (Intent == TEXT("ScanArea"))   return HandleScanArea(JsonObj);

	UE_LOG(LogTemp, Warning, TEXT("ProceduralCityManager: Unknown Intent '%s'"), *Intent);
	return BuildReceipt(TEXT("BuildResult"), TEXT("Failed"), TEXT(""),
		FVector::ZeroVector, FVector::ZeroVector,
		FString::Printf(TEXT("Unknown Intent: %s"), *Intent));
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  HandleSpawn — Create a single building
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FString AProceduralCityManager::HandleSpawn(TSharedPtr<FJsonObject> Json)
{
	// ── Parse ID ──────────────────────────────────────────────────
	FString ID;
	if (!Json->TryGetStringField(TEXT("ID"), ID) || ID.IsEmpty())
	{
		return BuildReceipt(TEXT("BuildResult"), TEXT("Failed"), TEXT(""),
			FVector::ZeroVector, FVector::ZeroVector,
			TEXT("Spawn requires a non-empty 'ID' field"));
	}

	UE_LOG(LogTemp, Log, TEXT("[CityManager] Received Spawn: ID='%s'"), *ID);

	// ── Duplicate guard ───────────────────────────────────────────
	if (Ledger.Contains(ID))
	{
		UE_LOG(LogTemp, Warning, TEXT("[CityManager] Duplicate ID '%s' — rejected"), *ID);
		return BuildReceipt(TEXT("BuildResult"), TEXT("Failed"), ID,
			FVector::ZeroVector, FVector::ZeroVector,
			FString::Printf(TEXT("ID '%s' already exists. Use Modify to change it."), *ID));
	}

	// ── Parse Style ─────────────────────────────────────────────
	FString StyleKey;
	if (!Json->TryGetStringField(TEXT("Style"), StyleKey))
	{
		StyleKey = TEXT("Default");
	}

	// ── Parse RequestedLoc ────────────────────────────────────────
	FVector RequestedLoc = FVector::ZeroVector;
	const TArray<TSharedPtr<FJsonValue>>* LocArr;
	if (Json->TryGetArrayField(TEXT("RequestedLoc"), LocArr) && LocArr->Num() >= 3)
	{
		RequestedLoc = JsonArrayToVector(*LocArr);
	}

	UE_LOG(LogTemp, Log, TEXT("[CityManager] '%s' requested at (%.0f, %.0f, %.0f)"),
		*ID, RequestedLoc.X, RequestedLoc.Y, RequestedLoc.Z);

	// ── Parse Parameters ─────────────────────────────────────────
	TSharedPtr<FJsonObject> Params;
	const TSharedPtr<FJsonObject>* ParamsPtr;
	if (Json->TryGetObjectField(TEXT("Parameters"), ParamsPtr))
	{
		Params = *ParamsPtr;
	}
	else
	{
		Params = MakeShared<FJsonObject>();
	}

	// ── Read StructureType ────────────────────────────────────────
	FString StructureType = TEXT("Building");
	Params->TryGetStringField(TEXT("StructureType"), StructureType);
	UE_LOG(LogTemp, Log, TEXT("[CityManager] '%s' StructureType='%s'"), *ID, *StructureType);

	// ── Environment Check / Auto-Nudge ────────────────────────────
	FVector ActualLoc = RequestedLoc;
	bool bNudged = false;

	const TSharedPtr<FJsonObject>* EnvCheck;
	if (Json->TryGetObjectField(TEXT("EnvironmentCheck"), EnvCheck))
	{
		bool bRequiresScan = false;
		(*EnvCheck)->TryGetBoolField(TEXT("RequiresScan"), bRequiresScan);

		if (bRequiresScan)
		{
			double RadiusD = 500.0;
			(*EnvCheck)->TryGetNumberField(TEXT("Radius"), RadiusD);
			float Radius = static_cast<float>(RadiusD);

			double Width = 1000.0, Depth = 1000.0;
			Params->TryGetNumberField(TEXT("BuildingWidth"), Width);
			Params->TryGetNumberField(TEXT("BuildingDepth"), Depth);
			Params->TryGetNumberField(TEXT("Width"), Width);
			Params->TryGetNumberField(TEXT("Depth"), Depth);
			FVector Extents(Width / 2.0, Depth / 2.0, 150.0);

			bool bFoundClear = false;
			ActualLoc = FindClearLocation(RequestedLoc, Radius, Extents, bFoundClear);

			if (!bFoundClear)
			{
				return BuildReceipt(TEXT("BuildResult"), TEXT("Failed"), ID,
					RequestedLoc, RequestedLoc,
					TEXT("Radius fully occupied - no clear location found"));
			}

			// Adjust Z to ground height
			float GroundZ = GetGroundZ(ActualLoc);
			ActualLoc.Z = GroundZ;

			bNudged = !ActualLoc.Equals(RequestedLoc, 1.0f);
		}
	}

	// ── Spawn the geometry ──────────────────────────────────────
	bool bSuccess = SpawnBuildingGeometry(ID, StyleKey, ActualLoc, Params);

	if (!bSuccess)
	{
		return BuildReceipt(TEXT("BuildResult"), TEXT("Failed"), ID,
			RequestedLoc, ActualLoc,
			TEXT("Failed to spawn building geometry"));
	}

	FString Status = bNudged ? TEXT("Success_Nudged") : TEXT("Success");
	UE_LOG(LogTemp, Log, TEXT("ProceduralCityManager: Spawned '%s' at (%.0f, %.0f, %.0f) [%s]"),
		*ID, ActualLoc.X, ActualLoc.Y, ActualLoc.Z, *Status);

	return BuildReceipt(TEXT("BuildResult"), Status, ID, RequestedLoc, ActualLoc);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  HandleBatchSpawn — Create multiple buildings from an array
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FString AProceduralCityManager::HandleBatchSpawn(TSharedPtr<FJsonObject> Json)
{
	const TArray<TSharedPtr<FJsonValue>>* Blueprints;
	if (!Json->TryGetArrayField(TEXT("Blueprints"), Blueprints))
	{
		return BuildReceipt(TEXT("BatchResult"), TEXT("Failed"), TEXT(""),
			FVector::ZeroVector, FVector::ZeroVector,
			TEXT("BatchSpawn requires a 'Blueprints' array"));
	}

	// Inherit top-level EnvironmentCheck for all blueprints
	TSharedPtr<FJsonObject> SharedEnvCheck;
	const TSharedPtr<FJsonObject>* EnvPtr;
	if (Json->TryGetObjectField(TEXT("EnvironmentCheck"), EnvPtr))
	{
		SharedEnvCheck = *EnvPtr;
	}

	// Build a results array
	TArray<TSharedPtr<FJsonValue>> ResultArray;

	for (const TSharedPtr<FJsonValue>& BpVal : *Blueprints)
	{
		const TSharedPtr<FJsonObject>* BpObj;
		if (!BpVal->TryGetObject(BpObj) || !(*BpObj).IsValid())
		{
			continue;
		}

		// Clone the blueprint object and inject shared EnvironmentCheck if missing
		TSharedPtr<FJsonObject> SpawnJson = MakeShared<FJsonObject>();
		for (const auto& Field : (*BpObj)->Values)
		{
			SpawnJson->SetField(Field.Key, Field.Value);
		}
		SpawnJson->SetStringField(TEXT("Intent"), TEXT("Spawn"));

		if (SharedEnvCheck.IsValid() && !SpawnJson->HasField(TEXT("EnvironmentCheck")))
		{
			SpawnJson->SetObjectField(TEXT("EnvironmentCheck"), SharedEnvCheck);
		}

		// Call HandleSpawn for this individual building — Ledger updates
		// INSIDE HandleSpawn before returning, so each subsequent blueprint
		// sees the updated world state (FIX: sequential ledger update)
		UE_LOG(LogTemp, Log, TEXT("[CityManager] BatchSpawn: processing blueprint %d/%d"),
			ResultArray.Num() + 1, Blueprints->Num());
		FString ReceiptStr = HandleSpawn(SpawnJson);

		// Parse the receipt back into a JSON object for the batch result
		TSharedRef<TJsonReader<>> RReader = TJsonReaderFactory<>::Create(ReceiptStr);
		TSharedPtr<FJsonObject> ReceiptObj;
		if (FJsonSerializer::Deserialize(RReader, ReceiptObj) && ReceiptObj.IsValid())
		{
			ResultArray.Add(MakeShared<FJsonValueObject>(ReceiptObj));
		}
	}

	// Build the BatchResult receipt
	TSharedPtr<FJsonObject> BatchReceipt = MakeShared<FJsonObject>();
	BatchReceipt->SetStringField(TEXT("Action"), TEXT("BatchResult"));
	BatchReceipt->SetArrayField(TEXT("Results"), ResultArray);

	FString Output;
	TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
		TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Output);
	FJsonSerializer::Serialize(BatchReceipt.ToSharedRef(), Writer);
	return Output;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  HandleModify — Destroy old building, rebuild with new params
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FString AProceduralCityManager::HandleModify(TSharedPtr<FJsonObject> Json)
{
	FString TargetID;
	if (!Json->TryGetStringField(TEXT("TargetID"), TargetID))
	{
		return BuildReceipt(TEXT("BuildResult"), TEXT("Failed"), TEXT(""),
			FVector::ZeroVector, FVector::ZeroVector,
			TEXT("Modify requires a 'TargetID' field"));
	}

	FProceduralBuilding* Existing = Ledger.Find(TargetID);
	if (!Existing)
	{
		return BuildReceipt(TEXT("BuildResult"), TEXT("Failed"), TargetID,
			FVector::ZeroVector, FVector::ZeroVector,
			FString::Printf(TEXT("ID '%s' not found in Ledger"), *TargetID));
	}

	// Store the original location before destruction
	FVector OriginalLocation = Existing->Location;

	// Destroy the old building (swap-and-pop safe)
	DestroyBuilding(TargetID);

	// Parse the new blueprint
	const TSharedPtr<FJsonObject>* NewBpPtr;
	if (!Json->TryGetObjectField(TEXT("NewBlueprint"), NewBpPtr))
	{
		return BuildReceipt(TEXT("BuildResult"), TEXT("Failed"), TargetID,
			OriginalLocation, OriginalLocation,
			TEXT("Modify requires a 'NewBlueprint' object"));
	}

	// Build a synthetic Spawn JSON
	TSharedPtr<FJsonObject> SpawnJson = MakeShared<FJsonObject>();
	SpawnJson->SetStringField(TEXT("Intent"), TEXT("Spawn"));
	SpawnJson->SetStringField(TEXT("ID"), TargetID);

	// Copy Style from new blueprint
	FString NewStyle;
	if ((*NewBpPtr)->TryGetStringField(TEXT("Style"), NewStyle))
	{
		SpawnJson->SetStringField(TEXT("Style"), NewStyle);
	}

	// Set location to original
	SpawnJson->SetArrayField(TEXT("RequestedLoc"), VectorToJsonArray(OriginalLocation));

	// Copy Parameters
	const TSharedPtr<FJsonObject>* NewParams;
	if ((*NewBpPtr)->TryGetObjectField(TEXT("Parameters"), NewParams))
	{
		SpawnJson->SetObjectField(TEXT("Parameters"), *NewParams);
	}

	// Spawn the new version at the same location
	return HandleSpawn(SpawnJson);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  HandleDestroy — Remove a single building
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FString AProceduralCityManager::HandleDestroy(TSharedPtr<FJsonObject> Json)
{
	FString TargetID;
	if (!Json->TryGetStringField(TEXT("TargetID"), TargetID))
	{
		return BuildReceipt(TEXT("BuildResult"), TEXT("Failed"), TEXT(""),
			FVector::ZeroVector, FVector::ZeroVector,
			TEXT("Destroy requires a 'TargetID' field"));
	}

	FProceduralBuilding* Existing = Ledger.Find(TargetID);
	if (!Existing)
	{
		return BuildReceipt(TEXT("BuildResult"), TEXT("Failed"), TargetID,
			FVector::ZeroVector, FVector::ZeroVector,
			FString::Printf(TEXT("ID '%s' not found in Ledger"), *TargetID));
	}

	FVector Location = Existing->Location;
	DestroyBuilding(TargetID);

	UE_LOG(LogTemp, Log, TEXT("ProceduralCityManager: Destroyed '%s'"), *TargetID);
	return BuildReceipt(TEXT("BuildResult"), TEXT("Destroyed"), TargetID,
		Location, Location);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  HandleClearAll — Wipe everything
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FString AProceduralCityManager::HandleClearAll()
{
	int32 Count = Ledger.Num();

	// Clear all HISM instances — O(1) per component
	for (auto& Pair : HISMPool)
	{
		if (Pair.Value)
		{
			Pair.Value->ClearInstances();
		}
	}

	Ledger.Empty();

	UE_LOG(LogTemp, Log, TEXT("ProceduralCityManager: ClearAll — removed %d buildings"), Count);

	// Return a receipt with the count
	TSharedPtr<FJsonObject> Receipt = MakeShared<FJsonObject>();
	Receipt->SetStringField(TEXT("Action"), TEXT("BuildResult"));
	Receipt->SetStringField(TEXT("Status"), TEXT("Cleared"));
	Receipt->SetNumberField(TEXT("BuildingsRemoved"), Count);

	FString Output;
	TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
		TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Output);
	FJsonSerializer::Serialize(Receipt.ToSharedRef(), Writer);
	return Output;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  HandleScanArea — Dual-Check: physics + Ledger scan
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FString AProceduralCityManager::HandleScanArea(TSharedPtr<FJsonObject> Json)
{
	// Parse Center
	FVector Center = FVector::ZeroVector;
	const TArray<TSharedPtr<FJsonValue>>* CenterArr;
	if (Json->TryGetArrayField(TEXT("Center"), CenterArr) && CenterArr->Num() >= 3)
	{
		Center = JsonArrayToVector(*CenterArr);
	}

	// Parse Radius
	double Radius = 500.0;
	Json->TryGetNumberField(TEXT("Radius"), Radius);

	// ── Check 1: Ground Height ──────────────────────────────────
	float GroundZ = GetGroundZ(Center);

	// ── Check 2: External Obstacles (Physics) ───────────────────
	TArray<FString> ExternalCollisions;
	{
		TArray<AActor*> FoundActors;
		TArray<TEnumAsByte<EObjectTypeQuery>> ObjectTypes;
		ObjectTypes.Add(UEngineTypes::ConvertToObjectType(ECC_WorldStatic));
		ObjectTypes.Add(UEngineTypes::ConvertToObjectType(ECC_WorldDynamic));

		TArray<AActor*> IgnoreActors;
		IgnoreActors.Add(this); // Don't detect ourselves

		UKismetSystemLibrary::BoxOverlapActors(
			GetWorld(), Center,
			FVector(Radius, Radius, Radius),
			ObjectTypes, nullptr, IgnoreActors,
			FoundActors);

		for (AActor* Actor : FoundActors)
		{
			if (Actor)
			{
				ExternalCollisions.Add(Actor->GetName());
			}
		}
	}

	// ── Check 3: Internal Obstacles (Ledger) ────────────────────
	TArray<FString> InternalCollisions;
	for (const auto& Pair : Ledger)
	{
		float Dist = FVector::Dist2D(Center, Pair.Value.Location);
		if (Dist < Radius)
		{
			InternalCollisions.Add(Pair.Key);
		}
	}

	UE_LOG(LogTemp, Log,
		TEXT("ProceduralCityManager: ScanArea at (%.0f,%.0f,%.0f) r=%.0f — GroundZ=%.1f, Ext=%d, Int=%d"),
		Center.X, Center.Y, Center.Z, Radius, GroundZ,
		ExternalCollisions.Num(), InternalCollisions.Num());

	return BuildScanReceipt(GroundZ, ExternalCollisions, InternalCollisions);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  SpawnBuildingGeometry — Routes by StructureType
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

bool AProceduralCityManager::SpawnBuildingGeometry(
	const FString& ID, const FString& StyleKey,
	FVector Location, TSharedPtr<FJsonObject> Params,
	TSharedPtr<FJsonObject> FullJson)
{
	FString StructureType = TEXT("Building");
	Params->TryGetStringField(TEXT("StructureType"), StructureType);

	// Route by StructureType
	if (StructureType.Equals(TEXT("Solid"), ESearchCase::IgnoreCase))
	{
		return SpawnSolidGeometry(ID, Location, Params);
	}
	else if (StructureType.Equals(TEXT("Composite"), ESearchCase::IgnoreCase))
	{
		// Parts array lives on the top-level JSON, not inside Parameters
		const TArray<TSharedPtr<FJsonValue>>* PartsArr = nullptr;
		if (FullJson.IsValid())
		{
			FullJson->TryGetArrayField(TEXT("Parts"), PartsArr);
		}
		if (!PartsArr)
		{
			Params->TryGetArrayField(TEXT("Parts"), PartsArr);
		}
		if (PartsArr)
		{
			return SpawnCompositeGeometry(ID, Location, Params, *PartsArr);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("[CityManager] '%s' Composite but no Parts array found, falling back to Building"), *ID);
		}
	}

	// Default: Building template (floors + walls + roof)
	UE_LOG(LogTemp, Log, TEXT("[CityManager] '%s' spawning as Building template"), *ID);

	// ── Resolve meshes and materials ────────────────────────────
	UStaticMesh* WallMesh = nullptr;
	UStaticMesh* FloorMesh = nullptr;
	UStaticMesh* RoofMesh = nullptr;
	UMaterialInterface* WallMat = nullptr;
	UMaterialInterface* FloorMat = nullptr;
	UMaterialInterface* RoofMat = nullptr;
	ResolveMeshes(StyleKey, WallMesh, FloorMesh, RoofMesh, WallMat, FloorMat, RoofMat);

	if (!WallMesh || !FloorMesh)
	{
		UE_LOG(LogTemp, Error, TEXT("[CityManager] Cannot resolve meshes for Style '%s'"), *StyleKey);
		return false;
	}

	auto* WallHISM = GetOrCreateHISM(WallMesh, WallMat);
	auto* FloorHISM = GetOrCreateHISM(FloorMesh, FloorMat);

	if (!WallHISM || !FloorHISM)
	{
		UE_LOG(LogTemp, Error, TEXT("[CityManager] Failed to create HISM components"));
		return false;
	}

	// ── Parse building parameters with defaults ─────────────────
	double NumFloorsD = 3.0;
	Params->TryGetNumberField(TEXT("Floors"), NumFloorsD);
	int32 NumFloors = FMath::Max(1, static_cast<int32>(NumFloorsD));

	double FloorHeight = 300.0;
	Params->TryGetNumberField(TEXT("FloorHeight"), FloorHeight);

	double BuildingWidth = 1000.0;
	Params->TryGetNumberField(TEXT("BuildingWidth"), BuildingWidth);

	double BuildingDepth = 1000.0;
	Params->TryGetNumberField(TEXT("BuildingDepth"), BuildingDepth);

	double WallThickness = 20.0;
	Params->TryGetNumberField(TEXT("WallThickness"), WallThickness);

	FString RoofType = TEXT("flat");
	Params->TryGetStringField(TEXT("RoofType"), RoofType);

	double HalfW = BuildingWidth / 2.0;
	double HalfD = BuildingDepth / 2.0;
	double SlabSX = BuildingWidth / 100.0;
	double SlabSY = BuildingDepth / 100.0;
	double SlabSZ = 0.2;
	double WallFBSX = BuildingWidth / 100.0;
	double WallFBSY = WallThickness / 100.0;
	double WallFBSZ = FloorHeight / 100.0;
	double WallLRSX = WallThickness / 100.0;
	double WallLRSY = BuildingDepth / 100.0;
	double WallLRSZ = FloorHeight / 100.0;
	double BaseX = Location.X;
	double BaseY = Location.Y;
	double BaseZ = Location.Z;

	FProceduralBuilding Building;
	Building.BuildingID = ID;
	Building.StyleKey = StyleKey;
	Building.Location = Location;

	for (int32 F = 0; F < NumFloors; ++F)
	{
		double FloorZ = BaseZ + (F * FloorHeight);
		double WallZ = FloorZ + (FloorHeight / 2.0);

		{
			FTransform T(FRotator::ZeroRotator, FVector(BaseX, BaseY, FloorZ), FVector(SlabSX, SlabSY, SlabSZ));
			int32 Idx = FloorHISM->AddInstance(T, true);
			Building.Instances.Add({FloorHISM, Idx});
		}
		{
			FTransform T(FRotator::ZeroRotator, FVector(BaseX, BaseY + HalfD, WallZ), FVector(WallFBSX, WallFBSY, WallFBSZ));
			int32 Idx = WallHISM->AddInstance(T, true);
			Building.Instances.Add({WallHISM, Idx});
		}
		{
			FTransform T(FRotator::ZeroRotator, FVector(BaseX, BaseY - HalfD, WallZ), FVector(WallFBSX, WallFBSY, WallFBSZ));
			int32 Idx = WallHISM->AddInstance(T, true);
			Building.Instances.Add({WallHISM, Idx});
		}
		{
			FTransform T(FRotator::ZeroRotator, FVector(BaseX - HalfW, BaseY, WallZ), FVector(WallLRSX, WallLRSY, WallLRSZ));
			int32 Idx = WallHISM->AddInstance(T, true);
			Building.Instances.Add({WallHISM, Idx});
		}
		{
			FTransform T(FRotator::ZeroRotator, FVector(BaseX + HalfW, BaseY, WallZ), FVector(WallLRSX, WallLRSY, WallLRSZ));
			int32 Idx = WallHISM->AddInstance(T, true);
			Building.Instances.Add({WallHISM, Idx});
		}
	}

	// Roof
	double RoofZ = BaseZ + (NumFloors * FloorHeight);
	if (RoofType.Equals(TEXT("pointed"), ESearchCase::IgnoreCase))
	{
		UStaticMesh* ActualRoofMesh = DefaultConeMesh;
		if (RoofMesh)
		{
			ActualRoofMesh = RoofMesh;
		}
		if (ActualRoofMesh)
		{
			auto* RoofHISM = GetOrCreateHISM(ActualRoofMesh, RoofMat);
			if (RoofHISM)
			{
				FTransform T(FRotator::ZeroRotator, FVector(BaseX, BaseY, RoofZ), FVector(SlabSX, SlabSY, 3.0));
				int32 Idx = RoofHISM->AddInstance(T, true);
				Building.Instances.Add({RoofHISM, Idx});
			}
		}
	}
	else
	{
		FTransform T(FRotator::ZeroRotator, FVector(BaseX, BaseY, RoofZ), FVector(SlabSX, SlabSY, SlabSZ));
		int32 Idx = FloorHISM->AddInstance(T, true);
		Building.Instances.Add({FloorHISM, Idx});
	}

	UE_LOG(LogTemp, Log, TEXT("[CityManager] '%s' Building: %d floors, %d HISM instances"),
		*ID, NumFloors, Building.Instances.Num());

	Ledger.Add(ID, MoveTemp(Building));
	return true;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  SpawnSolidGeometry — Single scaled primitive
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

bool AProceduralCityManager::SpawnSolidGeometry(
	const FString& ID, FVector Location, TSharedPtr<FJsonObject> Params)
{
	FString ShapeName = TEXT("cube");
	Params->TryGetStringField(TEXT("Shape"), ShapeName);

	UStaticMesh* Mesh = GetMeshForShape(ShapeName);
	if (!Mesh)
	{
		UE_LOG(LogTemp, Error, TEXT("[CityManager] '%s' Solid: unknown shape '%s'"), *ID, *ShapeName);
		return false;
	}

	double Width = 200.0, Depth = 200.0, Height = 200.0;
	Params->TryGetNumberField(TEXT("Width"), Width);
	Params->TryGetNumberField(TEXT("Depth"), Depth);
	Params->TryGetNumberField(TEXT("Height"), Height);

	double SX = Width / 100.0;
	double SY = Depth / 100.0;
	double SZ = Height / 100.0;

	// Center vertically
	FVector SpawnLoc = Location;
	SpawnLoc.Z += Height / 2.0;

	auto* HISM = GetOrCreateHISM(Mesh, nullptr);
	if (!HISM)
	{
		return false;
	}

	FTransform T(FRotator::ZeroRotator, SpawnLoc, FVector(SX, SY, SZ));
	int32 Idx = HISM->AddInstance(T, true);

	FProceduralBuilding Building;
	Building.BuildingID = ID;
	Building.StyleKey = TEXT("Solid");
	Building.Location = Location;
	Building.Instances.Add({HISM, Idx});

	Ledger.Add(ID, MoveTemp(Building));

	UE_LOG(LogTemp, Log, TEXT("[CityManager] '%s' Solid %s: %.0fx%.0fx%.0f UU (1 instance)"),
		*ID, *ShapeName, Width, Depth, Height);
	return true;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  SpawnCompositeGeometry — LLM-defined parts array
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

bool AProceduralCityManager::SpawnCompositeGeometry(
	const FString& ID, FVector Location,
	TSharedPtr<FJsonObject> Params,
	const TArray<TSharedPtr<FJsonValue>>& Parts)
{
	FProceduralBuilding Building;
	Building.BuildingID = ID;
	Building.StyleKey = TEXT("Composite");
	Building.Location = Location;

	int32 Spawned = 0;

	for (int32 i = 0; i < Parts.Num(); ++i)
	{
		const TSharedPtr<FJsonObject>* PartObj;
		if (!Parts[i]->TryGetObject(PartObj) || !(*PartObj).IsValid())
		{
			continue;
		}

		// Shape
		FString Shape = TEXT("cube");
		(*PartObj)->TryGetStringField(TEXT("Shape"), Shape);
		UStaticMesh* Mesh = GetMeshForShape(Shape);
		if (!Mesh)
		{
			UE_LOG(LogTemp, Warning, TEXT("[CityManager] '%s' Part %d: unknown shape '%s', skipping"),
				*ID, i, *Shape);
			continue;
		}

		// Offset (relative to base location)
		FVector Offset = FVector::ZeroVector;
		const TArray<TSharedPtr<FJsonValue>>* OffArr;
		if ((*PartObj)->TryGetArrayField(TEXT("Offset"), OffArr) && OffArr->Num() >= 3)
		{
			Offset = JsonArrayToVector(*OffArr);
		}

		// Scale
		FVector Scale = FVector::OneVector;
		const TArray<TSharedPtr<FJsonValue>>* ScaleArr;
		if ((*PartObj)->TryGetArrayField(TEXT("Scale"), ScaleArr) && ScaleArr->Num() >= 3)
		{
			Scale = JsonArrayToVector(*ScaleArr);
		}

		FVector WorldPos = Location + Offset;

		auto* HISM = GetOrCreateHISM(Mesh, nullptr);
		if (!HISM)
		{
			continue;
		}

		FTransform T(FRotator::ZeroRotator, WorldPos, Scale);
		int32 Idx = HISM->AddInstance(T, true);
		Building.Instances.Add({HISM, Idx});
		Spawned++;

		FString Label;
		if (!(*PartObj)->TryGetStringField(TEXT("Label"), Label))
		{
			Label = FString::Printf(TEXT("Part_%d"), i);
		}

		UE_LOG(LogTemp, Log, TEXT("[CityManager] '%s' Composite part %d '%s': %s at +(%.0f,%.0f,%.0f) scale(%.1f,%.1f,%.1f)"),
			*ID, i, *Label, *Shape, Offset.X, Offset.Y, Offset.Z, Scale.X, Scale.Y, Scale.Z);
	}

	if (Spawned == 0)
	{
		UE_LOG(LogTemp, Error, TEXT("[CityManager] '%s' Composite: 0 parts spawned"), *ID);
		return false;
	}

	Ledger.Add(ID, MoveTemp(Building));

	UE_LOG(LogTemp, Log, TEXT("[CityManager] '%s' Composite: %d/%d parts spawned"),
		*ID, Spawned, Parts.Num());
	return true;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  GetMeshForShape — Map shape name to engine mesh
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UStaticMesh* AProceduralCityManager::GetMeshForShape(const FString& ShapeName)
{
	FString Lower = ShapeName.ToLower();
	if (Lower == TEXT("cube") || Lower == TEXT("box"))       return DefaultCubeMesh;
	if (Lower == TEXT("sphere") || Lower == TEXT("ball"))    return DefaultSphereMesh;
	if (Lower == TEXT("cylinder") || Lower == TEXT("tube"))  return DefaultCylinderMesh;
	if (Lower == TEXT("cone") || Lower == TEXT("pyramid"))   return DefaultConeMesh;
	// Default to cube
	return DefaultCubeMesh;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  DestroyBuilding — Swap-and-Pop safe HISM instance removal
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

void AProceduralCityManager::DestroyBuilding(const FString& ID)
{
	FProceduralBuilding* Building = Ledger.Find(ID);
	if (!Building)
	{
		return;
	}

	// Group instances by their HISM component
	TMap<UHierarchicalInstancedStaticMeshComponent*, TArray<int32>> GroupedIndices;
	for (const FHISMInstanceRef& Ref : Building->Instances)
	{
		if (Ref.Component)
		{
			GroupedIndices.FindOrAdd(Ref.Component).Add(Ref.InstanceIndex);
		}
	}

	// For each component, remove indices in DESCENDING order
	// (critical for correct swap-and-pop behavior)
	for (auto& Pair : GroupedIndices)
	{
		UHierarchicalInstancedStaticMeshComponent* Comp = Pair.Key;
		TArray<int32>& Indices = Pair.Value;

		// Sort descending — remove highest first
		Indices.Sort([](int32 A, int32 B) { return A > B; });

		for (int32 Index : Indices)
		{
			int32 LastIdx = Comp->GetInstanceCount() - 1;

			if (Index > LastIdx)
			{
				// Index is out of bounds (shouldn't happen, but safety check)
				UE_LOG(LogTemp, Warning,
					TEXT("ProceduralCityManager: Skipping out-of-bounds index %d (count=%d) for '%s'"),
					Index, LastIdx + 1, *ID);
				continue;
			}

			if (Index != LastIdx)
			{
				// Swap-and-Pop: UE will move LastIdx into Index.
				// Find which other building owns LastIdx and update its tracking.
				SwapAndPopReindex(Comp, Index, LastIdx);
			}

			Comp->RemoveInstance(Index);
		}
	}

	// Remove from Ledger
	Ledger.Remove(ID);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  SwapAndPopReindex — Update the Ledger after RemoveInstance
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

void AProceduralCityManager::SwapAndPopReindex(
	UHierarchicalInstancedStaticMeshComponent* Component,
	int32 RemovedIndex, int32 OldLastIndex)
{
	// After RemoveInstance(RemovedIndex), UE swaps OldLastIndex into RemovedIndex.
	// Find whichever building owns OldLastIndex and update it to RemovedIndex.
	FProceduralBuilding* OwningBuilding = FindBuildingOwningIndex(Component, OldLastIndex);
	if (OwningBuilding)
	{
		for (FHISMInstanceRef& Ref : OwningBuilding->Instances)
		{
			if (Ref.Component == Component && Ref.InstanceIndex == OldLastIndex)
			{
				Ref.InstanceIndex = RemovedIndex;
				break; // There should only be one instance per index per component
			}
		}
	}
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  GetOrCreateHISM — Lazy HISM component pool
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UHierarchicalInstancedStaticMeshComponent* AProceduralCityManager::GetOrCreateHISM(
	UStaticMesh* Mesh, UMaterialInterface* Material)
{
	if (!Mesh)
	{
		return nullptr;
	}

	FHISMPoolKey Key;
	Key.Mesh = Mesh;
	Key.Material = Material;

	// Check if we already have an HISM for this {Mesh, Material} pair
	if (auto* Found = HISMPool.Find(Key))
	{
		return *Found;
	}

	// Create a new HISM component.
	// CRITICAL (Bug #2 fix): SetupAttachment BEFORE RegisterComponent.
	auto* NewHISM = NewObject<UHierarchicalInstancedStaticMeshComponent>(this);
	NewHISM->SetStaticMesh(Mesh);

	if (Material)
	{
		NewHISM->SetMaterial(0, Material);
	}

	NewHISM->SetMobility(EComponentMobility::Static);
	NewHISM->SetupAttachment(GetRootComponent());  // BEFORE registration
	NewHISM->RegisterComponent();                    // AFTER attachment

	HISMPool.Add(Key, NewHISM);
	return NewHISM;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ResolveMeshes — DataTable lookup with fallback
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

void AProceduralCityManager::ResolveMeshes(
	const FString& StyleKey,
	UStaticMesh*& OutWallMesh, UStaticMesh*& OutFloorMesh,
	UStaticMesh*& OutRoofMesh, UMaterialInterface*& OutWallMat,
	UMaterialInterface*& OutFloorMat, UMaterialInterface*& OutRoofMat)
{
	// Defaults
	OutWallMesh = DefaultCubeMesh;
	OutFloorMesh = DefaultCubeMesh;
	OutRoofMesh = DefaultConeMesh;
	OutWallMat = nullptr;
	OutFloorMat = nullptr;
	OutRoofMat = nullptr;

	// Try DataTable lookup
	if (AssetDictionary && !StyleKey.IsEmpty() && StyleKey != TEXT("Default"))
	{
		FAssetDictionaryRow* Row = AssetDictionary->FindRow<FAssetDictionaryRow>(
			FName(*StyleKey), TEXT("ResolveMeshes"));

		if (Row)
		{
			// Load soft object references
			if (!Row->WallMesh.IsNull())
			{
				UStaticMesh* Loaded = Row->WallMesh.LoadSynchronous();
				if (Loaded) OutWallMesh = Loaded;
			}
			if (!Row->FloorMesh.IsNull())
			{
				UStaticMesh* Loaded = Row->FloorMesh.LoadSynchronous();
				if (Loaded) OutFloorMesh = Loaded;
			}
			if (!Row->RoofMesh.IsNull())
			{
				UStaticMesh* Loaded = Row->RoofMesh.LoadSynchronous();
				if (Loaded) OutRoofMesh = Loaded;
			}
			if (!Row->WallMaterial.IsNull())
			{
				UMaterialInterface* Loaded = Row->WallMaterial.LoadSynchronous();
				if (Loaded) OutWallMat = Loaded;
			}
			if (!Row->FloorMaterial.IsNull())
			{
				UMaterialInterface* Loaded = Row->FloorMaterial.LoadSynchronous();
				if (Loaded) OutFloorMat = Loaded;
			}
			if (!Row->RoofMaterial.IsNull())
			{
				UMaterialInterface* Loaded = Row->RoofMaterial.LoadSynchronous();
				if (Loaded) OutRoofMat = Loaded;
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning,
				TEXT("ProceduralCityManager: Style '%s' not found in AssetDictionary — using fallback shapes"),
				*StyleKey);
		}
	}
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  Spatial Awareness — Dual-Check system
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FVector AProceduralCityManager::FindClearLocation(
	FVector Requested, float Radius, FVector BuildingExtents, bool& bOutFound)
{
	float MinClearance = FMath::Max(BuildingExtents.X, BuildingExtents.Y) * 1.5f;

	// First: check if the requested spot is already clear
	if (IsExternallyClear(Requested, BuildingExtents) &&
		IsInternallyClear(Requested, MinClearance))
	{
		bOutFound = true;
		return Requested;
	}

	// Spiral outward in concentric rings
	const float StepSize = 100.0f; // Check every 100 UU (1 meter)
	const int32 PointsPerRing = 8;

	for (float Dist = StepSize; Dist <= Radius; Dist += StepSize)
	{
		for (int32 i = 0; i < PointsPerRing; ++i)
		{
			float Angle = (2.0f * PI * i) / PointsPerRing;
			FVector Candidate = Requested + FVector(
				FMath::Cos(Angle) * Dist,
				FMath::Sin(Angle) * Dist,
				0.0f);

			if (IsExternallyClear(Candidate, BuildingExtents) &&
				IsInternallyClear(Candidate, MinClearance))
			{
				bOutFound = true;
				return Candidate;
			}
		}
	}

	// Entire radius exhausted — no clear spot
	bOutFound = false;
	return Requested;
}

bool AProceduralCityManager::IsExternallyClear(FVector Point, FVector Extents)
{
	TArray<AActor*> FoundActors;
	TArray<TEnumAsByte<EObjectTypeQuery>> ObjectTypes;
	ObjectTypes.Add(UEngineTypes::ConvertToObjectType(ECC_WorldStatic));

	TArray<AActor*> IgnoreActors;
	IgnoreActors.Add(this);

	UKismetSystemLibrary::BoxOverlapActors(
		GetWorld(), Point, Extents,
		ObjectTypes, nullptr, IgnoreActors,
		FoundActors);

	return FoundActors.Num() == 0;
}

bool AProceduralCityManager::IsInternallyClear(FVector Point, float MinDistance)
{
	for (const auto& Pair : Ledger)
	{
		float Dist = FVector::Dist2D(Point, Pair.Value.Location);
		if (Dist < MinDistance)
		{
			return false;
		}
	}
	return true;
}

float AProceduralCityManager::GetGroundZ(FVector Location)
{
	FHitResult Hit;
	FVector Start = FVector(Location.X, Location.Y, 10000.0f);
	FVector End = FVector(Location.X, Location.Y, -10000.0f);

	FCollisionQueryParams Params;
	Params.AddIgnoredActor(this);

	if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_WorldStatic, Params))
	{
		return Hit.ImpactPoint.Z;
	}

	return Location.Z; // No ground found — keep original Z
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  JSON Receipt Builders
//  All use FJsonSerializer::Serialize for proper escaping (Bug #5 fix).
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FString AProceduralCityManager::BuildReceipt(
	const FString& Action, const FString& Status,
	const FString& ID, FVector RequestedLoc, FVector ActualLoc,
	const FString& Reason)
{
	TSharedPtr<FJsonObject> Receipt = MakeShared<FJsonObject>();
	Receipt->SetStringField(TEXT("Action"), Action);
	Receipt->SetStringField(TEXT("Status"), Status);

	if (!ID.IsEmpty())
	{
		Receipt->SetStringField(TEXT("ID"), ID);
	}

	Receipt->SetArrayField(TEXT("RequestedLoc"), VectorToJsonArray(RequestedLoc));
	Receipt->SetArrayField(TEXT("ActualLoc"), VectorToJsonArray(ActualLoc));

	if (!Reason.IsEmpty())
	{
		Receipt->SetStringField(TEXT("Reason"), Reason);
	}

	FString Output;
	TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
		TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Output);
	FJsonSerializer::Serialize(Receipt.ToSharedRef(), Writer);
	return Output;
}

FString AProceduralCityManager::BuildScanReceipt(
	float GroundZ,
	const TArray<FString>& ExternalCollisions,
	const TArray<FString>& InternalCollisions)
{
	TSharedPtr<FJsonObject> Receipt = MakeShared<FJsonObject>();
	Receipt->SetStringField(TEXT("Action"), TEXT("ScanResult"));

	FString Status = (ExternalCollisions.Num() == 0 && InternalCollisions.Num() == 0)
		? TEXT("Clear") : TEXT("Occupied");
	Receipt->SetStringField(TEXT("Status"), Status);
	Receipt->SetNumberField(TEXT("GroundZ"), GroundZ);

	// External collisions array
	TArray<TSharedPtr<FJsonValue>> ExtArr;
	for (const FString& Name : ExternalCollisions)
	{
		ExtArr.Add(MakeShared<FJsonValueString>(Name));
	}
	Receipt->SetArrayField(TEXT("ExternalCollisions"), ExtArr);

	// Internal collisions array
	TArray<TSharedPtr<FJsonValue>> IntArr;
	for (const FString& Name : InternalCollisions)
	{
		IntArr.Add(MakeShared<FJsonValueString>(Name));
	}
	Receipt->SetArrayField(TEXT("InternalCollisions"), IntArr);

	FString Output;
	TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
		TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Output);
	FJsonSerializer::Serialize(Receipt.ToSharedRef(), Writer);
	return Output;
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  Utility Functions
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FProceduralBuilding* AProceduralCityManager::FindBuildingOwningIndex(
	UHierarchicalInstancedStaticMeshComponent* Component, int32 Index)
{
	for (auto& Pair : Ledger)
	{
		for (const FHISMInstanceRef& Ref : Pair.Value.Instances)
		{
			if (Ref.Component == Component && Ref.InstanceIndex == Index)
			{
				return &Pair.Value;
			}
		}
	}
	return nullptr;
}

FVector AProceduralCityManager::JsonArrayToVector(const TArray<TSharedPtr<FJsonValue>>& Arr)
{
	if (Arr.Num() < 3) return FVector::ZeroVector;
	return FVector(
		Arr[0]->AsNumber(),
		Arr[1]->AsNumber(),
		Arr[2]->AsNumber());
}

TArray<TSharedPtr<FJsonValue>> AProceduralCityManager::VectorToJsonArray(FVector Vec)
{
	TArray<TSharedPtr<FJsonValue>> Arr;
	Arr.Add(MakeShared<FJsonValueNumber>(Vec.X));
	Arr.Add(MakeShared<FJsonValueNumber>(Vec.Y));
	Arr.Add(MakeShared<FJsonValueNumber>(Vec.Z));
	return Arr;
}

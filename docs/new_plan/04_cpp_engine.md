# 🏗️ The C++ Engine — AProceduralCityManager Explained

> This document explains every component of the C++ master builder class that lives inside Unreal Engine. If you've never written Unreal C++, start here.

---

## What Is It?

`AProceduralCityManager` is a single Unreal Engine Actor that you place in your level. It acts as the brain, hands, and memory of the building system inside the engine. When Python sends a JSON command over WebSocket, this actor receives it, parses it, calculates geometry, and spawns HISM instances.

Think of it as a **construction foreman** sitting in your level, waiting for blueprints to arrive.

---

## The Files

| File | Purpose |
|------|---------|
| `ProceduralBuildingTypes.h` | All data structures (UStructs) used by the system |
| `ProceduralCityManager.h` | The actor class declaration (what functions and properties exist) |
| `ProceduralCityManager.cpp` | The actor implementation (how everything works) |

These files are generated into the `generated/` folder. You copy them into your Unreal project's `Source/` directory and compile.

> **Important:** All files use `{{PROJECT_API}}` as the export macro. When Python generates them, it replaces this with your project's actual macro (e.g., `MYPROJECT_API`). Set `PROJECT_API=MYPROJECT_API` in your `.env` file.

---

## The Data Structures (ProceduralBuildingTypes.h)

### FHISMInstanceRef — "Where Is This Piece?"

Tracks a single HISM instance within a component.

```cpp
USTRUCT()
struct FHISMInstanceRef
{
    GENERATED_BODY()

    // Which HISM component holds this instance
    UPROPERTY()
    UHierarchicalInstancedStaticMeshComponent* Component;

    // The index within that component's instance array
    UPROPERTY()
    int32 InstanceIndex;
};
```

**Why this exists:** A building is made of many pieces (floor slabs, walls, roof). Each piece is an "instance" in an HISM component. To modify or delete a building later, we need to know exactly which instances belong to it.

### FProceduralBuilding — "What Did We Build?"

The Ledger entry. One per building.

```cpp
USTRUCT()
struct FProceduralBuilding
{
    GENERATED_BODY()

    UPROPERTY()
    FString BuildingID;        // "ProcBldg_01"

    UPROPERTY()
    FString StyleKey;          // "House_Wood_Small"

    UPROPERTY()
    FString OriginalJson;      // The full JSON used to create this building

    UPROPERTY()
    FVector Location;          // Where it was actually placed (may differ from requested)

    UPROPERTY()
    TArray<FHISMInstanceRef> Instances;  // All HISM pieces belonging to this building
};
```

### FAssetDictionaryRow — "What Does This Style Look Like?"

A DataTable row. Maps a semantic Style tag to actual Unreal meshes and materials.

```cpp
USTRUCT()
struct FAssetDictionaryRow : public FTableRowBase
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere)
    TSoftObjectPtr<UStaticMesh> WallMesh;

    UPROPERTY(EditAnywhere)
    TSoftObjectPtr<UStaticMesh> FloorMesh;

    UPROPERTY(EditAnywhere)
    TSoftObjectPtr<UStaticMesh> RoofMesh;     // Used for pointed roofs

    UPROPERTY(EditAnywhere)
    TSoftObjectPtr<UMaterialInterface> WallMaterial;

    UPROPERTY(EditAnywhere)
    TSoftObjectPtr<UMaterialInterface> FloorMaterial;

    UPROPERTY(EditAnywhere)
    TSoftObjectPtr<UMaterialInterface> RoofMaterial;
};
```

**How it works:**
1. You create a DataTable in the Unreal Editor
2. Each row's name is a Style key (e.g., `"House_Wood_Small"`)
3. Each row points to the actual Static Meshes and Materials
4. C++ looks up the Style tag from the LLM's JSON, finds the row, loads the assets

**If the DataTable is empty or missing:** C++ falls back to `/Engine/BasicShapes/Cube` and `/Engine/BasicShapes/Cone`. The system always works — even without custom assets.

---

## The Actor Class (ProceduralCityManager.h)

### Key Properties

```cpp
UCLASS(Blueprintable, Placeable)
class YOURPROJECT_API AProceduralCityManager : public AActor
{
    GENERATED_BODY()

public:
    // ── The Main Entry Point ────────────────────────────────────
    // Python calls this via WebSocket Remote Control API
    UFUNCTION(BlueprintCallable, Category = "Procedural")
    FString ProcessBlueprint(const FString& JsonPayload);

protected:
    // ── Assets ──────────────────────────────────────────────────
    // Optional DataTable mapping Style tags to meshes/materials
    UPROPERTY(EditDefaultsOnly, Category = "Assets")
    UDataTable* AssetDictionary;

    // Fallback meshes (loaded in constructor)
    UPROPERTY()
    UStaticMesh* DefaultCubeMesh;   // Walls, floors, flat roofs

    UPROPERTY()
    UStaticMesh* DefaultConeMesh;   // Pointed roofs

    // ── State ───────────────────────────────────────────────────
    // The Ledger — tracks every building by ID
    UPROPERTY(VisibleAnywhere, Category = "State")
    TMap<FString, FProceduralBuilding> Ledger;

    // Pool of HISM components — one per unique {mesh + material} pair
    // Keyed by FHISMPoolKey (composite of mesh + material) so different
    // material styles on the same mesh get separate HISM components.
    UPROPERTY()
    TMap<FHISMPoolKey, UHierarchicalInstancedStaticMeshComponent*> HISMPool;
};
```

---

## The Math Loop — How Buildings Are Constructed

This is a direct translation of the Python math from `processor.py::_handle_spawn_actor()`.

### The Concept

A building is made of:
- **Floor slabs** — Flat cubes at the base of each story
- **Walls** — Thin cubes on the 4 perimeter edges of each story
- **Roof** — Either a flat slab (same as floor) or a cone on top

### The Constants

```
Default cube in Unreal = 100 × 100 × 100 Unreal Units (UU)
1 UU ≈ 1 centimeter
So: 100 UU = 1 meter

FloorHeight = 300 UU = 3 meters per story
BuildingWidth = 1000 UU = 10 meters wide
WallThickness = 20 UU = 20 centimeters thick
```

### Scale Factor Calculation

Since the default cube is 100×100×100 UU, we divide desired dimensions by 100 to get scale factors:

```
Floor slab scale:
  SX = BuildingWidth / 100    (e.g., 1000/100 = 10.0)
  SY = BuildingDepth / 100    (e.g., 1000/100 = 10.0)
  SZ = 0.2                    (thin slab = 20 UU tall)

Front/Back wall scale:
  SX = BuildingWidth / 100    (full width)
  SY = WallThickness / 100    (thin, e.g., 20/100 = 0.2)
  SZ = FloorHeight / 100      (e.g., 300/100 = 3.0)

Left/Right wall scale:
  SX = WallThickness / 100    (thin)
  SY = BuildingDepth / 100    (full depth)
  SZ = FloorHeight / 100      (full height)
```

### The Loop (Pseudocode)

> ⚠️ **CRITICAL:** All `AddInstance` calls MUST use `bWorldSpace = true` (the second parameter). HISM instances default to component-local space. Since our math produces absolute world coordinates, omitting this flag would offset every building by the CityManager actor's position.

```
for floor = 0 to (NumFloors - 1):
    floor_z = base_z + (floor × FloorHeight)
    wall_z  = floor_z + (FloorHeight / 2)    // center of wall

    // Floor slab at the base of this story
    // NOTE: bWorldSpace = true is MANDATORY — coordinates are absolute
    HISM->AddInstance(FTransform(Location(base_x, base_y, floor_z), Scale(slab_sx, slab_sy, 0.2)), true)

    // Front wall (Y + half_depth)
    HISM->AddInstance(FTransform(Location(base_x, base_y + half_d, wall_z), Scale(...)), true)

    // Back wall (Y - half_depth)
    HISM->AddInstance(FTransform(Location(base_x, base_y - half_d, wall_z), Scale(...)), true)

    // Left wall (X - half_width)
    HISM->AddInstance(FTransform(Location(base_x - half_w, base_y, wall_z), Scale(...)), true)

    // Right wall (X + half_width)
    HISM->AddInstance(FTransform(Location(base_x + half_w, base_y, wall_z), Scale(...)), true)

// Roof
roof_z = base_z + (NumFloors × FloorHeight)
if RoofType == "flat":
    HISM->AddInstance(FTransform(Location(base_x, base_y, roof_z), Scale(slab_sx, slab_sy, 0.2)), true)
else if RoofType == "pointed":
    HISM->AddInstance(FTransform(Location(base_x, base_y, roof_z), Scale(slab_sx, slab_sy, 3.0)), true)
```

### Per-Floor Actor Count

| Component | Count per Floor |
|-----------|----------------|
| Floor slab | 1 |
| Front wall | 1 |
| Back wall | 1 |
| Left wall | 1 |
| Right wall | 1 |
| **Total per floor** | **5** |

Plus 1 roof on top. So a 5-floor building = (5 × 5) + 1 = **26 HISM instances**.

But unlike the old system where each instance was a separate actor with its own draw call, HISM renders all wall instances in a single draw call, all floor instances in a single draw call, etc. Maximum 3 draw calls for 26 instances (cubeHISM + coneHISM).

---

## The HISM Pool — Dynamic Component Management

The `AProceduralCityManager` doesn't create HISM components upfront. It creates them **lazily** when needed.

```cpp
// The pool uses a composite key: {Mesh + Material}
// This ensures different materials on the same mesh get separate HISM components.
UHierarchicalInstancedStaticMeshComponent* AProceduralCityManager::GetOrCreateHISM(
    UStaticMesh* Mesh, UMaterialInterface* Material /*= nullptr*/)
{
    FHISMPoolKey Key{Mesh, Material};

    // Check if we already have an HISM for this {mesh, material} pair
    if (auto** Found = HISMPool.Find(Key))
    {
        return *Found;
    }

    // Create a new one
    // ⚠️ CRITICAL: SetupAttachment MUST come BEFORE RegisterComponent.
    //    AttachToComponent is for already-registered components.
    //    Using them in the wrong order causes invisible/orphaned components.
    auto* NewHISM = NewObject<UHierarchicalInstancedStaticMeshComponent>(this);
    NewHISM->SetStaticMesh(Mesh);
    if (Material)
    {
        NewHISM->SetMaterial(0, Material);
    }
    NewHISM->SetMobility(EComponentMobility::Static);
    NewHISM->SetupAttachment(GetRootComponent());   // BEFORE registration
    NewHISM->RegisterComponent();                     // AFTER attachment setup

    HISMPool.Add(Key, NewHISM);
    return NewHISM;
}
```

**Why lazy creation?** We don't know in advance which meshes will be needed. The DataTable might have 50 different wall meshes, but this particular scene only uses 3. Lazy creation avoids allocating unused components.

---

## Discovering the Manager from Python

Python doesn't know your Unreal level structure. It discovers the manager at runtime:

1. Call `GetAllLevelActors` on `EditorActorSubsystem`
2. Filter for actors whose path contains `"ProceduralCityManager"`
3. Cache the full object path
4. Use that path for all subsequent `ProcessBlueprint` calls

If the manager isn't found, Python raises a clear error:
```
❌ No AProceduralCityManager found in the level.
   Please place one in your map (drag from Content Browser).
```

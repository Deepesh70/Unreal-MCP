# 👁️ Spatial Awareness — The Dual-Check ScanArea System

> How Unreal Engine "sees" the world before it builds, and how it automatically avoids obstacles.

---

## The Problem

Basic procedural generation is **blind**. You tell it "build a house at X:100" and it builds there — even if there's a mountain, a lake, or another building already occupying that space. The result: clipping geometry, floating structures, and overlapping buildings.

To build intelligently, the system needs **eyes** — the ability to look at a location and understand what's already there.

---

## Why Standard Physics Traces Don't Work Alone

In a normal Unreal project, you'd use `BoxOverlapActors()` or `LineTraceMulti()` to detect objects at a location. And for **regular actors** (landscape meshes, BSP geometry, placed static meshes), this works perfectly.

**But our procedural buildings are NOT regular actors.**

Our buildings are HISM instances — they're rendered by a single `AProceduralCityManager` actor. If you run a `BoxOverlapActors` trace at a location where five procedural buildings stand, Unreal will tell you:

```
Overlap found: ProceduralCityManager_0
```

Just one actor. It can't tell you WHICH specific building you hit, or whether the overlap is with Building A or Building B. HISM instances are **invisible to the physics system** as individual entities.

---

## The Solution: Dual-Check Scanning

We split collision detection into two completely separate systems:

### Check 1: External Obstacles (Physics-Based)

For objects that **are** regular actors — things you placed manually in the level or that the terrain system created:

| Object Type | How It's Detected |
|-------------|-------------------|
| Landscape (terrain) | Line trace downward → GroundZ |
| BSP brushes (rocks, hills) | BoxOverlapActors |
| Manually placed StaticMeshActors | BoxOverlapActors |
| Blocking volumes | BoxOverlapActors |
| Water bodies | BoxOverlapActors |

**Implementation:**
```cpp
// Ground height detection
FHitResult Hit;
FVector TraceStart = FVector(Center.X, Center.Y, 10000.0f);
FVector TraceEnd   = FVector(Center.X, Center.Y, -10000.0f);
bool bHit = GetWorld()->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_WorldStatic);
float GroundZ = bHit ? Hit.ImpactPoint.Z : 0.0f;

// Box overlap for obstacles
TArray<AActor*> FoundActors;
TArray<TEnumAsByte<EObjectTypeQuery>> ObjectTypes;
ObjectTypes.Add(UEngineTypes::ConvertToObjectType(ECC_WorldStatic));
UKismetSystemLibrary::BoxOverlapActors(
    GetWorld(), Center, FVector(Radius),
    ObjectTypes, nullptr, TArray<AActor*>{this},  // Ignore self (CityManager)
    FoundActors
);
```

### Check 2: Internal Obstacles (Memory-Based)

For objects that **are** HISM instances — our own procedural buildings stored in the Ledger:

```cpp
TArray<FString> InternalCollisions;
float MinClearance = FMath::Max(BuildingWidth, BuildingDepth) * 0.75f;

for (const auto& Pair : Ledger)
{
    float Distance = FVector::Dist(Center, Pair.Value.Location);
    if (Distance < MinClearance)
    {
        InternalCollisions.Add(Pair.Key);  // "ProcBldg_01"
    }
}
```

**Why this is better than physics:**
- **100% accurate:** We know the exact location and footprint of every building because we stored it
- **Computationally cheaper:** `FVector::Dist()` is a single square root. No broad-phase/narrow-phase physics pipeline
- **Returns building IDs:** We know exactly WHICH building is blocking, not just "something is there"

---

## The ScanArea Receipt

When Python sends a `ScanArea` intent, C++ performs both checks and returns a combined report:

```json
{
  "Action": "ScanResult",
  "Status": "Occupied",
  "GroundZ": 150.5,
  "ExternalCollisions": ["Landscape_0", "Rock_BSP_3"],
  "InternalCollisions": ["ProcBldg_01", "ProcBldg_07"]
}
```

The LLM can use this information to plan its layout before committing to a `Spawn` or `BatchSpawn`.

---

## Auto-Nudge — Automatic Obstacle Avoidance

When a `Spawn` or `BatchSpawn` request includes `"EnvironmentCheck": {"RequiresScan": true, "Radius": 500}`, C++ automatically runs the Dual-Check and resolves conflicts.

### The Spiral Search Algorithm

If the requested location is blocked, C++ searches outward in a spiral pattern:

```
Step 1: Check requested point (0, 0)
Step 2: Check 8 points at distance 100:
        (100,0) (71,71) (0,100) (-71,71) (-100,0) (-71,-71) (0,-100) (71,-71)
Step 3: Check 8 points at distance 200:
        (200,0) (141,141) ... etc
Step 4: Continue until Radius is exceeded
```

```cpp
FVector AProceduralCityManager::FindClearLocation(
    FVector Requested, float MaxRadius, FVector BuildingExtents)
{
    // First: check if the requested spot is clear
    if (IsExternallyClear(Requested, BuildingExtents) &&
        IsInternallyClear(Requested, BuildingExtents.GetMax()))
    {
        return Requested;  // No nudge needed
    }

    // Spiral outward
    float StepSize = 100.0f;  // Check every 100 UU (1 meter)
    int32 PointsPerRing = 8;

    for (float Dist = StepSize; Dist <= MaxRadius; Dist += StepSize)
    {
        for (int32 i = 0; i < PointsPerRing; ++i)
        {
            float Angle = (2.0f * PI * i) / PointsPerRing;
            FVector Candidate = Requested + FVector(
                FMath::Cos(Angle) * Dist,
                FMath::Sin(Angle) * Dist,
                0.0f  // Keep same Z, adjust later with GroundZ
            );

            if (IsExternallyClear(Candidate, BuildingExtents) &&
                IsInternallyClear(Candidate, BuildingExtents.GetMax()))
            {
                return Candidate;
            }
        }
    }

    // Entire radius is blocked
    return FVector::ZeroVector;  // Signals failure to caller
}
```

### The Nudge Receipt

```json
{
  "Action": "BuildResult",
  "Status": "Success_Nudged",
  "ID": "ProcBldg_01",
  "RequestedLoc": [100, 0, 0],
  "ActualLoc": [300, 0, 150.5],
  "Reason": "Nudged 200 UU from requested location due to obstacle"
}
```

Python passes this receipt back to the LLM, so the AI knows where the building actually ended up. This is crucial for planning — if the LLM is placing houses along a street, it needs to know the actual coordinates of each one to calculate the next gap.

---

## Ground Height Adjustment

Even when no obstacles are present, buildings should sit ON the ground, not float above it or sink into it.

When `RequiresScan` is true:
1. C++ performs a line trace downward at the build location
2. The `GroundZ` value replaces the Z-component of the build location
3. This ensures buildings are always flush with the terrain

```
Requested:  [100, 0, 0]     ← Z=0, but the terrain at X:100 is a hill
GroundZ:    150.5            ← The line trace found the ground at Z=150.5
ActualLoc:  [100, 0, 150.5] ← Building placed on the hillside
```

---

## BatchSpawn and Internal Overlap

When processing a `BatchSpawn` array, C++ spawns buildings **sequentially**. Each building is added to the Ledger immediately after spawning. This means:

- Building 1 is spawned and registered
- When Building 2 is processed, the Dual-Check sees Building 1 in the Ledger
- If Building 2's location overlaps Building 1, it gets auto-nudged

This prevents buildings within the same batch from overlapping each other — a problem that would be invisible if you only checked against pre-existing buildings.

---

## When Scanning Is NOT Used

If `EnvironmentCheck.RequiresScan` is `false` or omitted, the building is spawned **blindly** at the exact requested coordinates. This is useful when:

- The LLM has already performed a `ScanArea` and calculated safe coordinates
- You're debugging and want exact placement
- Performance matters and you trust the coordinates

---

## Performance Considerations

| Operation | Cost |
|-----------|------|
| Line trace for GroundZ | ~0.01 ms per trace |
| BoxOverlapActors | ~0.05 ms per check |
| Ledger iteration (1000 buildings) | ~0.1 ms (pure math) |
| Full spiral search (50 candidates) | ~5 ms worst case |

Even the worst case (50 spiral candidates × full Dual-Check) completes in under 5 milliseconds. This is well within a single frame budget (16.67 ms at 60 FPS).

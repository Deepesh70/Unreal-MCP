# 📋 The JSON Contract — Complete Data Schema

> This is the single source of truth for all data flowing between the LLM, Python, and Unreal C++. If you change a field here, you must update all three layers.

---

## Design Principles

1. **The LLM dictates Style; Unreal dictates Assets.** The LLM never writes `/Game/Materials/M_Brick`. It writes `"Style": "House_Brick"`. Unreal resolves that to actual meshes.
2. **Every building has an ID.** No anonymous spawning. The Ledger tracks everything by ID.
3. **Parameters are optional.** C++ uses sensible defaults. The LLM should only override what matters.
4. **One Intent per payload (except BatchSpawn).** Keep routing logic simple.

---

## The 6 Intents

### 1. `Spawn` — Create a Single Building

Creates one building at a specified location.

```json
{
  "Intent": "Spawn",
  "ID": "ProcBldg_01",
  "Style": "House_Wood_Small",
  "EnvironmentCheck": {
    "RequiresScan": true,
    "Radius": 500
  },
  "RequestedLoc": [0, 0, 0],
  "Parameters": {
    "Floors": 3,
    "FloorHeight": 300,
    "BuildingWidth": 1000,
    "BuildingDepth": 1000,
    "WallThickness": 20,
    "RoofType": "flat"
  }
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `Intent` | string | ✅ | — | Must be `"Spawn"` |
| `ID` | string | ✅ | — | Unique identifier. LLM generates this. Format: `ProcBldg_XX` or any descriptive string |
| `Style` | string | ❌ | `"Default"` | Semantic tag mapped to meshes/materials via DataTable |
| `EnvironmentCheck.RequiresScan` | bool | ❌ | `false` | If true, C++ checks for obstacles and auto-nudges |
| `EnvironmentCheck.Radius` | float | ❌ | `500` | Maximum distance C++ can nudge the building (in Unreal Units) |
| `RequestedLoc` | float[3] | ✅ | — | `[X, Y, Z]` coordinates in Unreal Units |
| `Parameters.Floors` | int | ❌ | `3` | Number of stories |
| `Parameters.FloorHeight` | float | ❌ | `300` | Height per story in UU (300 UU ≈ 3 meters) |
| `Parameters.BuildingWidth` | float | ❌ | `1000` | X-axis dimension in UU |
| `Parameters.BuildingDepth` | float | ❌ | `1000` | Y-axis dimension in UU |
| `Parameters.WallThickness` | float | ❌ | `20` | Wall thickness in UU |
| `Parameters.RoofType` | string | ❌ | `"flat"` | `"flat"` = slab on top. `"pointed"` = cone/pyramid |

---

### 2. `BatchSpawn` — Create Multiple Buildings

Creates an array of buildings in a single call. Used for neighborhoods, streets, city blocks.

```json
{
  "Intent": "BatchSpawn",
  "EnvironmentCheck": {
    "RequiresScan": true,
    "Radius": 500
  },
  "Blueprints": [
    {
      "ID": "Bldg_Left",
      "Style": "House_Wood_Small",
      "RequestedLoc": [0, -1000, 0],
      "Parameters": { "Floors": 1, "RoofType": "pointed" }
    },
    {
      "ID": "Bldg_Right",
      "Style": "Office_Concrete_Large",
      "RequestedLoc": [0, 1000, 0],
      "Parameters": { "Floors": 5, "RoofType": "flat" }
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `Intent` | string | ✅ | Must be `"BatchSpawn"` |
| `EnvironmentCheck` | object | ❌ | Applied to ALL blueprints in the batch unless individually overridden |
| `Blueprints` | array | ✅ | Array of building specifications. Each follows the same schema as `Spawn` (minus the `Intent` field) |

**Processing Order:** C++ processes blueprints sequentially. Each building's auto-nudge considers previously spawned buildings in the same batch (they're already in the Ledger by the time the next one is processed).

---

### 3. `Modify` — Change an Existing Building

Destroys the old building and rebuilds it with new parameters at the same location.

```json
{
  "Intent": "Modify",
  "TargetID": "ProcBldg_01",
  "NewBlueprint": {
    "Style": "Office_Concrete_Large",
    "Parameters": {
      "Floors": 10,
      "RoofType": "flat"
    }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `Intent` | string | ✅ | Must be `"Modify"` |
| `TargetID` | string | ✅ | The ID of the building to modify. Must exist in the Ledger |
| `NewBlueprint` | object | ✅ | New Style and Parameters. The building keeps its original location |

**Internal Logic:**
1. Look up `TargetID` in the Ledger
2. Store the original location
3. Call `DestroyBuilding(TargetID)` — swap-and-pop safe removal
4. Call `HandleSpawn()` with the new blueprint + same ID + original location
5. Return receipt

---

### 4. `Destroy` — Remove a Single Building

```json
{
  "Intent": "Destroy",
  "TargetID": "ProcBldg_01"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `Intent` | string | ✅ | Must be `"Destroy"` |
| `TargetID` | string | ✅ | The ID of the building to remove |

**Receipt on success:**
```json
{ "Action": "BuildResult", "Status": "Destroyed", "ID": "ProcBldg_01" }
```

**Receipt on failure (ID not found):**
```json
{ "Action": "BuildResult", "Status": "Failed", "ID": "ProcBldg_01", "Reason": "ID not found in Ledger" }
```

---

### 5. `ClearAll` — Remove Everything

```json
{ "Intent": "ClearAll" }
```

No parameters. Wipes every HISM instance and empties the Ledger.

**C++ Logic:**
```cpp
for (auto& Pair : HISMPool)
{
    Pair.Value->ClearInstances();
}
Ledger.Empty();
```

**Receipt:**
```json
{ "Action": "BuildResult", "Status": "Cleared", "BuildingsRemoved": 42 }
```

---

### 6. `ScanArea` — Look Before You Build

A read-only query. Does not modify anything. Returns information about what's at a location.

```json
{
  "Intent": "ScanArea",
  "Center": [100, 0, 0],
  "Radius": 500
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `Intent` | string | ✅ | Must be `"ScanArea"` |
| `Center` | float[3] | ✅ | The center of the area to scan |
| `Radius` | float | ✅ | The radius to scan (in UU) |

**Receipt:**
```json
{
  "Action": "ScanResult",
  "Status": "Occupied",
  "GroundZ": 150.5,
  "ExternalCollisions": ["Landscape_0", "Rock_BSP_3"],
  "InternalCollisions": ["ProcBldg_01", "ProcBldg_07"]
}
```

| Receipt Field | Description |
|--------------|-------------|
| `GroundZ` | The Z-height of the ground at the center point (from line trace) |
| `ExternalCollisions` | Non-procedural actors found via physics trace (Landscape, BSP, StaticMeshActors) |
| `InternalCollisions` | Procedural buildings found via Ledger distance check (`FVector::Dist`). NOT from physics. |

---

## Default Values Reference

When the LLM omits optional parameters, C++ uses these defaults:

| Parameter | Default Value | Real-World Equivalent |
|-----------|--------------|----------------------|
| `Floors` | 3 | A typical house |
| `FloorHeight` | 300 UU | 3 meters |
| `BuildingWidth` | 1000 UU | 10 meters |
| `BuildingDepth` | 1000 UU | 10 meters |
| `WallThickness` | 20 UU | 20 centimeters |
| `RoofType` | `"flat"` | Modern/industrial roof |
| `Style` | `"Default"` | Gray basic shapes (fallback) |
| `EnvironmentCheck.RequiresScan` | `false` | Blind spawn (no collision check) |
| `EnvironmentCheck.Radius` | 500 UU | 5-meter nudge radius |

---

## Style Tags (Semantic Dictionary)

The LLM uses semantic tags. These are mapped to actual Unreal assets via the C++ DataTable.

### Built-in Styles (Always Available)
| Style Tag | Fallback Mesh | Description |
|-----------|--------------|-------------|
| `"Default"` | Basic Cube/Cone | Gray untextured geometry |

### Suggested Style Tags (User Populates DataTable)
| Style Tag | Intended Look |
|-----------|--------------|
| `"House_Wood_Small"` | Small wooden house with wood-textured walls |
| `"House_Brick_Medium"` | Medium brick house |
| `"Office_Concrete_Large"` | Large concrete office building |
| `"Office_Glass_Tower"` | Glass-walled skyscraper |
| `"Industrial_Steel"` | Steel/metal warehouse |
| `"Cyberpunk_Neon"` | Neon-lit futuristic panels |

The LLM can invent any Style tag it wants. If the tag doesn't exist in the DataTable, C++ gracefully falls back to `"Default"` (basic shapes) and logs a warning.

---

## Legacy Compatibility

The old JSON format (used before The Great Refactor) is still supported:

```json
{
  "Action": "SpawnActor",
  "ClassToSpawn": "Building",
  "Parameters": { "NumberOfFloors": 5, "X": 0, "Y": 0, "Z": 0 }
}
```

Python's `process_agent_output()` auto-migrates this to the new format:
```json
{
  "Intent": "Spawn",
  "ID": "Legacy_Building_<timestamp>",
  "Style": "Default",
  "RequestedLoc": [0, 0, 0],
  "Parameters": { "Floors": 5 }
}
```

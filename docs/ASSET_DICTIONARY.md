# Asset Dictionary — DataTable Setup Guide

> How to map Style tags to actual Unreal meshes and materials for
> visually rich procedural buildings.

---

## What Is It?

The Asset Dictionary is an **optional** Unreal DataTable that maps the
LLM's semantic `Style` tags (like `"House_Wood_Small"`) to actual
Static Meshes and Materials in your project.

**Without it:** All buildings use Unreal's default gray Cube and Cone
basic shapes. The system works perfectly — just looks plain.

**With it:** Buildings use your custom meshes (wooden walls, brick
textures, glass panels, etc.) for visually rich environments.

---

## Step 1: Create the DataTable

1. Open the **Unreal Editor**
2. In the **Content Browser**, right-click → **Miscellaneous** → **Data Table**
3. When prompted for the Row Structure, select **`FAssetDictionaryRow`**
   - If you don't see it, make sure you've compiled the generated C++ files
4. Name it something like `DT_AssetDictionary`
5. Save

---

## Step 2: Add Rows

Each row in the DataTable represents one Style:

1. Double-click `DT_AssetDictionary` to open it
2. Click **"Add"** to create a new row
3. Set the **Row Name** to match the Style tag the LLM will use:
   - `House_Wood_Small`
   - `House_Brick_Medium`
   - `Office_Concrete_Large`
   - `Office_Glass_Tower`
   - `Industrial_Steel`
   - etc.

4. For each row, fill in the fields:

| Field | What To Set |
|-------|------------|
| `WallMesh` | Your wall Static Mesh (e.g., `SM_WoodWall`) |
| `FloorMesh` | Your floor Static Mesh (e.g., `SM_WoodFloor`) |
| `RoofMesh` | Mesh for pointed roofs (e.g., `SM_WoodRoof`). Flat roofs use `FloorMesh`. |
| `WallMaterial` | Material for walls (e.g., `M_Wood`) |
| `FloorMaterial` | Material for floors |
| `RoofMaterial` | Material for roofs |

> **Tip:** You can leave fields empty. Any empty field falls back to
> the default engine basic shape.

---

## Step 3: Assign to the City Manager

1. Select the **`ProceduralCityManager`** actor in your level
2. In the **Details** panel, find the **Assets** category
3. Set **`AssetDictionary`** to your `DT_AssetDictionary`
4. Save

---

## Step 4: Test

```bash
python agent.py groq -b -i
🏗️ Builder > Build a wooden house at 0 0 0
```

If `House_Wood_Small` exists in your DataTable, the house will use
your custom meshes. If not, it falls back to gray cubes with a warning
in the UE Output Log.

---

## Fallback Behavior

| Scenario | What Happens |
|----------|-------------|
| DataTable not assigned (null) | All buildings use `/Engine/BasicShapes/Cube` and `/Cone` |
| Style tag not found in DataTable | Same fallback + warning in UE Output Log |
| Style tag found but mesh field is empty | That specific part uses the fallback mesh |
| Style tag found and mesh field is set | Custom mesh is used ✅ |

---

## Style Tag Naming Convention

The LLM can invent any Style tag it wants. To keep things organized:

```
<Type>_<Material>_<Size>

Examples:
  House_Wood_Small
  House_Brick_Medium
  House_Stone_Large
  Office_Concrete_Small
  Office_Glass_Tower
  Industrial_Steel_Warehouse
  Cyberpunk_Neon_Panel
```

---

## Adding New Styles

1. Create the meshes/materials in Unreal
2. Add a new row to the DataTable with the Style tag as the row name
3. Assign the meshes/materials to the row fields
4. Save — no C++ recompilation needed!

The DataTable is hot-reloadable. You can add new styles while the
MCP server is running. The next build command will pick them up.

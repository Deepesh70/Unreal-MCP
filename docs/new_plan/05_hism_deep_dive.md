# ⚡ HISM Deep Dive — Why It Matters and How Swap-and-Pop Works

> This is the most critical technical document in the project. If you don't understand HISM and its deletion behavior, you will ship bugs that are nearly impossible to debug.

---

## What Is HISM?

HISM stands for **Hierarchical Instanced Static Mesh Component** (`UHierarchicalInstancedStaticMeshComponent`). It's Unreal Engine's most efficient way to render many copies of the same mesh.

### The Draw Call Problem

In a 3D engine, a **draw call** is a command sent from the CPU to the GPU saying "draw this mesh at this location." Each draw call has overhead (state changes, buffer binds, shader switches). The GPU is fast at drawing — but the CPU bottlenecks on issuing too many draw calls.

| Approach | 100 Walls | Draw Calls | FPS Impact |
|----------|-----------|------------|------------|
| 100 separate StaticMeshActors | 100 actors | ~100 | 🔴 Heavy |
| 1 InstancedStaticMesh with 100 instances | 1 component | ~1 | 🟢 Minimal |
| 1 HISM with 100 instances | 1 component | ~1 (with LOD) | 🟢 Minimal + LOD |

### ISM vs HISM

| Feature | ISM | HISM |
|---------|-----|------|
| Single draw call for all instances | ✅ | ✅ |
| LOD (Level of Detail) support | ❌ | ✅ |
| Culling of off-screen instances | ❌ | ✅ |
| Performance at 10,000+ instances | ⚠️ Degrades | ✅ Excellent |

HISM organizes instances into a spatial hierarchy (a tree structure) so the engine can efficiently cull instances that aren't visible to the camera. This is why we use HISM, not plain ISM.

---

## How HISM Stores Instances

Internally, an HISM component manages an **array of transforms**:

```
Index 0: FTransform(Location: 0,0,0,     Scale: 10,10,0.2)     ← Floor slab
Index 1: FTransform(Location: 0,500,150,  Scale: 10,0.2,3)      ← Front wall
Index 2: FTransform(Location: 0,-500,150, Scale: 10,0.2,3)      ← Back wall
Index 3: FTransform(Location: -500,0,150, Scale: 0.2,10,3)      ← Left wall
Index 4: FTransform(Location: 500,0,150,  Scale: 0.2,10,3)      ← Right wall
```

When you call `AddInstance(FTransform)`, it appends to the end and returns the new index.

When you call `GetInstanceCount()`, it returns the total number of instances.

---

## 🚨 The Swap-and-Pop Problem (CRITICAL)

### What Happens When You Delete an Instance?

When you call `RemoveInstance(int32 Index)`, Unreal does **NOT** shift all subsequent indices down by one (like removing from the middle of a standard array). That would be O(n) and too slow for thousands of instances.

Instead, Unreal uses **Swap-and-Pop:**

1. Take the **last element** in the array
2. **Move it** into the slot of the removed element
3. **Truncate** the array by one

### Visual Example

```
BEFORE: RemoveInstance(1)
┌───────┬───────┬───────┬───────┬───────┐
│ Idx 0 │ Idx 1 │ Idx 2 │ Idx 3 │ Idx 4 │
│ Floor │ Wall  │ Wall  │ Wall  │ Wall  │
│  (A)  │  (A)  │  (B)  │  (B)  │  (B)  │
└───────┴───────┴───────┴───────┴───────┘
         ↑ REMOVE THIS          ↑ LAST ELEMENT

Step 1: Swap last (4) into removed slot (1)
┌───────┬───────┬───────┬───────┬───────┐
│ Idx 0 │ Idx 1 │ Idx 2 │ Idx 3 │ Idx 4 │
│ Floor │ Wall  │ Wall  │ Wall  │       │
│  (A)  │  (B)← │  (B)  │  (B)  │ EMPTY │
└───────┴───────┴───────┴───────┴───────┘

Step 2: Pop the last slot
┌───────┬───────┬───────┬───────┐
│ Idx 0 │ Idx 1 │ Idx 2 │ Idx 3 │
│ Floor │ Wall  │ Wall  │ Wall  │
│  (A)  │  (B)  │  (B)  │  (B)  │
└───────┴───────┴───────┴───────┘

RESULT: The instance that WAS at index 4 is NOW at index 1
```

### Why This Breaks Naive Tracking

If Building B was tracking its instances as `[2, 3, 4]` and we removed index 1 (from Building A), Building B's actual indices are now `[2, 3, 1]` — but Building B's ledger still says `[2, 3, 4]`. Index 4 no longer exists. If you later try to `RemoveInstance(4)`, you'll crash or corrupt memory.

---

## The Correct Deletion Algorithm

### DestroyBuilding (Single Building)

```
function DestroyBuilding(BuildingID):
    Building = Ledger[BuildingID]

    // Group instances by HISM component
    GroupedByComponent = GroupBy(Building.Instances, ref => ref.Component)

    for each (Component, InstanceRefs) in GroupedByComponent:
        // Sort indices DESCENDING — remove highest first
        Sort(InstanceRefs by InstanceIndex, Descending)

        for each Ref in InstanceRefs:
            Index = Ref.InstanceIndex
            LastIdx = Component->GetInstanceCount() - 1

            if Index == LastIdx:
                // We're removing the last element — just pop, no swap needed
                Component->RemoveInstance(Index)
            else:
                // Swap-and-Pop will happen: last element moves to Index
                // Find which building owns LastIdx
                OwnerBuilding = FindBuildingOwningIndex(Component, LastIdx)
                
                if OwnerBuilding is valid AND OwnerBuilding != Building:
                    // Update the owner: their instance moved from LastIdx → Index
                    OwnerBuilding.UpdateInstanceIndex(Component, LastIdx, Index)

                Component->RemoveInstance(Index)

    // Remove building from Ledger
    Ledger.Remove(BuildingID)
```

### Why Descending Order?

Removing the highest index first is critical:

1. If the highest index IS the last element → no swap happens (just pop)
2. If it's not the last → the element swapped in came from an even higher index, which we either already removed or don't care about
3. As we work downward, the array shrinks from the end, keeping lower indices stable until we reach them

### FindBuildingOwningIndex Helper

```cpp
FProceduralBuilding* FindBuildingOwningIndex(UHISMC* Component, int32 Index)
{
    for (auto& Pair : Ledger)
    {
        for (auto& Ref : Pair.Value.Instances)
        {
            if (Ref.Component == Component && Ref.InstanceIndex == Index)
            {
                return &Pair.Value;
            }
        }
    }
    return nullptr;
}
```

This is O(n × m) where n = buildings and m = average instances per building. For typical city sizes (hundreds of buildings), this is fast enough. For massive cities (10,000+ buildings), we'd optimize with a reverse lookup `TMap<UHISMC*, TMap<int32, FString>>`.

---

## ClearAll — The Easy Path

When you want to remove EVERYTHING, you don't need to worry about swap-and-pop at all:

```cpp
for (auto& Pair : HISMPool)
{
    Pair.Value->ClearInstances();   // Removes ALL instances at once
}
Ledger.Empty();
```

`ClearInstances()` is O(1) — it just resets the internal array. No per-instance tracking needed.

---

## Performance Characteristics

| Operation | Time Complexity | Notes |
|-----------|----------------|-------|
| `AddInstance()` | O(1) amortized | Array append |
| `RemoveInstance()` | O(1) swap-and-pop + O(n) tree rebuild | Tree rebuild happens automatically |
| `ClearInstances()` | O(1) | Resets everything |
| `GetInstanceCount()` | O(1) | Returns array length |
| Our `DestroyBuilding()` | O(k × n) | k = instances in building, n = total buildings in ledger |

### Memory Usage

Each HISM instance stores:
- Transform (Location + Rotation + Scale) = 10 floats = 40 bytes
- Custom data (optional) = variable
- Internal tree node references = ~16 bytes

A 5-floor building = 26 instances ≈ 26 × 56 bytes ≈ **1.5 KB**
A 1,000-building city ≈ 26,000 instances ≈ **1.5 MB**
A 10,000-building metropolis ≈ 260,000 instances ≈ **15 MB**

This is trivial. HISM can handle millions of instances.

---

## Common Pitfalls

### ❌ Pitfall 1: Decrementing All Indices Above the Removed One
```
WRONG: for all buildings, if index > removedIndex, index -= 1
This is how std::vector works, NOT how UE HISM works.
UE uses swap-and-pop. Only the LAST index changes.
```

### ❌ Pitfall 2: Removing Instances Without Updating the Ledger
```
WRONG: Component->RemoveInstance(3); // don't update tracking
Later: Component->RemoveInstance(4); // index 4 no longer exists → CRASH
```

### ❌ Pitfall 3: Removing Instances in Ascending Order
```
WRONG: Remove index 1, then index 3
After removing 1: old index 4 is now at 1. Array = [0, 4, 2, 3]
Now remove "index 3": you're removing old-index-3, which is correct...
BUT: the element swapped into index 1 has a new identity. If index 3
was also being removed, it's still at 3 — but the Ledger may be stale.

CORRECT: Remove index 3 first, then index 1.
```

### ✅ The Golden Rule
**Always find who owns the last index BEFORE calling RemoveInstance. Update their tracking AFTER the removal.**

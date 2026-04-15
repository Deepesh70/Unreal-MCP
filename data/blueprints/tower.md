# 3-Story Tower: Semantic Architecture Specification

This blueprint defines the structural logic for a 3-story tower. Instead of raw coordinates, it uses **Semantic Snapping** to ensure perfect alignment regardless of asset scale.

## Phase 1: Ground Floor
1.  **Spawn `floor`** (Label: `foundation`) at the origin.
2.  **Spawn 4 `walls`**. 
3.  **Snap** them to the `north`, `south`, `east`, and `west` edges of the `foundation`.
4.  **Spawn `stairs`**. 
5.  **Snap** them to the `southwest` corner of the `foundation`.

## Phase 2: Second Level
1.  **Spawn `floor`** (Label: `floor_2`).
2.  **Snap** `floor_2` to the `top` of the `north_wall_ground` (or any ground wall).
3.  **Spawn 4 `walls`** for level 2.
4.  **Snap** them to the `north`, `south`, `east`, and `west` edges of `floor_2`.
5.  **Spawn `stairs`** for level 2.
6.  **Snap** them to the `northeast` corner of `floor_2`.

## Phase 3: Third Level & Roof
1.  **Spawn `floor`** (Label: `floor_3`).
2.  **Snap** `floor_3` to the `top` of the level 2 walls.
3.  **Spawn 4 `walls`** for level 3.
4.  **Snap** them to the `north`, `south`, `east`, and `west` edges of `floor_3`.
5.  **Spawn `cube`** (Label: `roof_cap`).
6.  **Snap** `roof_cap` to the `top` of the level 3 walls and scale it to cover the top.

## Execution Directives:
- Priority: Use `snap_to_actor` for every alignment step. 
- Math: Do NOT attempt to calculate manual XYZ offsets in Phase 2 or 3.

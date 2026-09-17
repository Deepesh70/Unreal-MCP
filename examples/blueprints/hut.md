# Wooden Hut Architecture: Exact Coordinate Specification

This document defines the strict geometric parameters for generating a 3D wooden hut. Do not estimate, guess, or eyeball coordinates or scales. Assume the base primitive for all objects is a standard 100x100x100 unit cube centered at its pivot.

All coordinates (X, Y, Z) represent the EXACT center pivot of the object in world space.

## 1. Floor Base
- **Dimensions:** 400 (X-depth) x 400 (Y-width) x 20 (Z-thickness).
- **Scale:** `X: 4.0, Y: 4.0, Z: 0.2`
- **Location:** `X: 0, Y: 0, Z: -10`
- **Logic:** Placing the Z-center at -10 ensures the top surface of the floor is perfectly flush at Z=0. This establishes a clean ground plane for the walls.

## 2. Four Exterior Walls
The walls must form a perfect 400x400 perimeter without overlapping at the corners. The walls are 20 units thick and 300 units high. 

**North Wall (+X Edge)**
- **Dimensions:** 20 (X-depth) x 400 (Y-width) x 300 (Z-height).
- **Scale:** `X: 0.2, Y: 4.0, Z: 3.0`
- **Location:** `X: 190, Y: 0, Z: 150`
- **Logic:** Center X is 190 so the outer face sits precisely at X=200, perfectly flush with the floor's edge.

**South Wall (-X Edge)**
- **Dimensions:** 20 (X-depth) x 400 (Y-width) x 300 (Z-height).
- **Scale:** `X: 0.2, Y: 4.0, Z: 3.0`
- **Location:** `X: -190, Y: 0, Z: 150`
- **Logic:** Mirrors the North wall exactly on the opposite side.

**East Wall (+Y Edge)**
- **Dimensions:** 360 (X-depth) x 20 (Y-width) x 300 (Z-height).
- **Scale:** `X: 3.6, Y: 0.2, Z: 3.0`
- **Location:** `X: 0, Y: 190, Z: 150`
- **Logic:** The X-depth is strictly 360 (not 400). This allows the East wall to slot perfectly *between* the 20-unit thick North and South walls without Z-fighting or overlapping corners.

**West Wall (-Y Edge)**
- **Dimensions:** 360 (X-depth) x 20 (Y-width) x 300 (Z-height).
- **Scale:** `X: 3.6, Y: 0.2, Z: 3.0`
- **Location:** `X: 0, Y: -190, Z: 150`
- **Logic:** Mirrors the East wall.

## 3. Door Cutout
- Do not attempt to build the North wall out of multiple complex sub-blocks. 
- **Instruction:** Generate a solid block acting as a boolean subtractor or a visually distinct door placeholder.
- **Dimensions:** 20 (X-depth) x 120 (Y-width) x 210 (Z-height).
- **Scale:** `X: 0.25, Y: 1.2, Z: 2.1`
- **Location:** `X: 190, Y: 0, Z: 105`
- **Logic:** Z=105 rests the bottom of the 210-high door exactly at Z=0 (the floor surface).

## 4. Sloped A-Frame Roof
The roof uses exact trigonometric calculations for a 30-degree pitch to ensure the lower edges rest flawlessly on the top outer corners of the walls (Z=300), and the top edges meet exactly at the apex (Y=0).

- **Dimensions (per panel):** 400 (X-depth) x 230.94 (Y-width) x 20 (Z-thickness).
- **Scale:** `X: 4.0, Y: 2.3094, Z: 0.2`

**Right Roof Panel (+Y Side)**
- **Location:** `X: 0, Y: 3100, Z: 357.73`
- **Rotation:** `Roll: -30.0` degrees (Pitch: 0, Yaw: 0)

**Left Roof Panel (-Y Side)**
- **Location:** `X: 0, Y: -100, Z: 357.73`
- **Rotation:** `Roll: 30.0` degrees (Pitch: 0, Yaw: 0)

## Build Order Execution:
1. Spawn Floor.
2. Spawn North and South walls (Full width).
3. Spawn East and West walls (Inner width).
4. Spawn Door volume.
5. Spawn Left and Right Roof panels with precise rotation and Z-elevation.
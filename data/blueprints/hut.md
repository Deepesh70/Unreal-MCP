# Wooden Hut Architecture

A classic wooden hut or cabin is composed of a floor, four surrounding exterior walls, and a sloped roof.

## Components:
1. **Floor Base**
   - A flat rectangular slab.
   - Example dimensions: 400 wide x 400 deep, but only 10 or 20 units thick.
   - Placed exactly at Z=0.

2. **Four Walls**
   - The North, South, East, and West exterior walls.
   - They must be tall (e.g., 250 to 300 units).
   - They run along the extreme boundary edges of the floor base. Do not place them in the center coordinates.
   - If the floor is 400 units wide, the walls must be placed at X=200 and X=-200 so they align perfectly with the edges.
   - The Z coordinate must be half the height of the walls (e.g., if height is 300, Z=150) so they rest exactly on the floor, not sinking through it.
   - Ensure the East and West walls are slightly shorter on the Y-axis so they slot neatly *between* the North and South walls without overlapping corners.

3. **Door Cutout / Gap**
   - You can leave a gap in the front wall for a door, or spawn a separate smaller cube (door) inside the front wall.
   
4. **Sloped A-Frame Roof**
   - A roof consists of TWO separate flat slabs (e.g. `sx: 4.0, sy: 2.5, sz: 0.2`).
   - IMPORTANT: In Unreal Engine, objects rotate around their **center point**. 
   - If you place two roof panels at the exact same X,Y,Z coordinates and rotate them, they will intersect in the middle and form an "X" shape!
   - To form an A-frame resting on the walls, you MUST offset their X or Y coordinates so they meet at the top apex.
   - For example: if the hut center is X=0, Y=0:
     - Left roof panel: Place at Y=-100, rotated (roll=30)
     - Right roof panel: Place at Y=100, rotated (roll=-30)
   - The Z height of the roof center must be higher than the walls so it covers them (e.g., if walls are 300, roof Z should be 350).

## Build Order:
- Floor first.
- Four walls precisely calculated to align exactly with the mathematical edges of the floor.
- Rotated roof pieces placed precisely on top of the wall coordinates.

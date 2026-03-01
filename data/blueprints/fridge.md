# Standard Refrigerator Blueprint

A standard kitchen refrigerator is composed of two main geometric components stacked vertically.

## Components:
1. **Lower Body (Fridge)**
   - The main cooling section.
   - It is a tall, wide box.
   - Dimensions are roughly 100 wide x 100 deep x 140 tall.
   - It sits on the floor (Z=0).

2. **Upper Body (Freezer)**
   - The freezer section sitting exactly on top of the lower body.
   - Same width and depth as the lower body, but shorter.
   - Dimensions are roughly 100 wide x 100 deep x 60 tall.
   - Because the lower body is 140 tall, you must place the freezer starting at Z=140 so it perfectly connects without a gap.

3. **Handles**
   - Two thin columns on the left or right side of the doors to open them.
   - Placed slightly in front of the main body on the Y axis.

## Build Order:
- Place the Fridge body on the ground.
- Place the Freezer body precisely stacked on top of the Fridge body by adding the height of the fridge to its Z coordinate.
- Add small handles to the front edges of both.

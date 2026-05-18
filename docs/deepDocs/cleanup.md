Python Cleanup Script & Headless Compiler Wrapper
Currently, setup_unreal.py copies generated C++ files into the Unreal project, and relies on the user opening the Editor to compile them. If compilation fails (e.g. LNK2019 missing module or C1083 cannot open include file), the Unreal project is left in a corrupted state, failing to launch.

Goal
Create a Python script that acts as a headless compiler wrapper and cleanup script. If the compiler fails with a fatal error, it should automatically delete the generated .h and .cpp files to restore the project to a working state (Garbage Collection).

Proposed Changes
[NEW] scripts/compile_and_clean.py
A new script that:

Takes the path to a .uproject (or auto-discovers it).
Locates the UnrealBuildTool (UBT) from the engine installation.
Invokes UBT to compile the project headlessly.
Monitors the output for fatal errors (LNK2019, C1083, error C2, etc.).
If a fatal error occurs, immediately deletes the generated files (ProceduralCityManager.h, ProceduralCityManager.cpp, ProceduralBuildingTypes.h) from the Source/<Project> directory to prevent corruption.
[MODIFY] setup_unreal.py
Update setup_unreal.py to optionally invoke this headless compile script, or at least point the user to it instead of manual compilation.
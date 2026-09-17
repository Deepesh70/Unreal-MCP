"""
Backward compatibility launcher for scripts/setup_materials.py.
The canonical location is `scripts/setup_materials.py`.
"""
import os
import runpy

if __name__ == "__main__":
    target = os.path.join(os.path.dirname(__file__), *['scripts', 'setup_materials.py'])
    runpy.run_path(target, run_name="__main__")

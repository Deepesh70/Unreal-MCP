"""
Backward compatibility launcher for examples/demos/demo_unreal.py.
The canonical location is `examples/demos/demo_unreal.py`.
"""
import os
import runpy

if __name__ == "__main__":
    target = os.path.join(os.path.dirname(__file__), *['examples', 'demos', 'demo_unreal.py'])
    runpy.run_path(target, run_name="__main__")

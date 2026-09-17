"""
Backward compatibility launcher for scripts/build_relay.py.
The canonical location is `scripts/build_relay.py`.
"""
import os
import runpy

if __name__ == "__main__":
    target = os.path.join(os.path.dirname(__file__), *['scripts', 'build_relay.py'])
    runpy.run_path(target, run_name="__main__")

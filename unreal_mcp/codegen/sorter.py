from collections import deque, defaultdict
from typing import List, Dict

def resolve_build_order(llm_manifest: dict) -> List[str]:
    """
    Takes a JSON manifest of C++ modules and their dependencies.
    Returns a strict, linear list of module names in the exact order they must be compiled.
    """
    modules_list = llm_manifest.get("modules", [])
    
    # 1. Initialize Graph and In-Degree structures
    in_degree = {mod["name"]: 0 for mod in modules_list}
    graph = defaultdict(list)
    
    # 2. Build the Directed Acyclic Graph (DAG)
    for mod in modules_list:
        u = mod["name"]
        deps = mod.get("dependencies", [])
        
        for v in deps:
            if v not in in_degree:
                raise ValueError(f"CRITICAL ERROR: LLM hallucinated a dependency '{v}' that does not exist.")
            
            # v must be compiled BEFORE u. 
            # The directed edge goes from v -> u
            graph[v].append(u)
            in_degree[u] += 1
            
    # 3. Queue up modules with NO dependencies (The base layers)
    queue = deque([u for u in in_degree if in_degree[u] == 0])
    compile_order = []
    
    # 4. Kahn's Algorithm: Process the queue
    while queue:
        node = queue.popleft()
        compile_order.append(node)
        
        # Once a base module is compiled, remove its requirement from its children
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            # If the child now has 0 uncompiled dependencies, it is ready to build
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                
    # 5. The Circular Dependency Kill-Switch
    if len(compile_order) != len(modules_list):
        raise RuntimeError(
            "CIRCULAR DEPENDENCY DETECTED. The LLM generated an impossible loop "
            "(e.g., Module A depends on B, but B depends on A). Build aborted to prevent engine crash."
        )
        
    return compile_order

# --- Quick Local Test ---
if __name__ == "__main__":
    dummy_payload = {
      "modules": [
        {"name": "WeaponModule", "dependencies": ["InventoryModule", "CoreStatsModule"]},
        {"name": "CoreStatsModule", "dependencies": []},
        {"name": "InventoryModule", "dependencies": ["CoreStatsModule"]}
      ]
    }
    
    # Even though WeaponModule is listed first in the JSON, the math forces it to the end.
    safe_order = resolve_build_order(dummy_payload)
    print(f"Mathematical Compile Order: {safe_order}")
    # Output: ['CoreStatsModule', 'InventoryModule', 'WeaponModule']
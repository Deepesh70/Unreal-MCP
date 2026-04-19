# 🧠 Token-Aware Complexity Routing

> How the system handles massive, complex scene requests by intelligently splitting them across multiple LLM calls.

---

## The Problem

When a user says "build a detailed medieval village with 40 unique buildings, a town square, walls, and a gate," the LLM needs to output a `BatchSpawn` JSON with 40 detailed building specifications. Each building spec is roughly 150-250 tokens:

```
40 buildings × 200 tokens average = 8,000 tokens of output
```

But LLMs have **output token limits:**

| Model | Max Output Tokens |
|-------|------------------|
| Groq (Llama 3.3 70B) | ~4,096 |
| Gemini 2.5 Pro | ~8,192 |
| Ollama (varies) | 2,048 - 8,192 |

If the required output exceeds the model's limit, the JSON will be truncated. `_repair_truncated_json()` can save the structure, but the building data itself is lost — you'll get 20 buildings instead of 40, and the last building's data will be incomplete.

---

## The Solution: The Orchestrator

The Orchestrator (`agents/orchestrator.py`) sits between the user's prompt and the LLM. It estimates complexity, decides whether to split, and manages multi-call generation.

### The Flow

```
User: "Build a medieval village with 40 buildings"
                    │
                    ▼
          ┌──────────────────┐
          │  ORCHESTRATOR    │
          │                  │
          │  Estimate: ~8000 │
          │  tokens needed   │
          │                  │
          │  Model max: 4096 │
          │                  │
          │  Decision: SPLIT │
          │  into 3 chunks   │
          └──┬───┬───┬───────┘
             │   │   │
             ▼   ▼   ▼
         Chunk 1  Chunk 2  Chunk 3
         "North   "Center  "South
         district  square   district
         14 bldgs  market   14 bldgs
         + walls"  12 bldgs + gate"
             │       │       │
             ▼       ▼       ▼
          LLM call LLM call LLM call
          ~3500    ~3200    ~3500
          tokens   tokens   tokens
             │       │       │
             ▼       ▼       ▼
          Validate Validate Validate
          + Repair + Repair + Repair
             │       │       │
             ▼       ▼       ▼
          BatchSpawn BatchSpawn BatchSpawn
          → Unreal   → Unreal  → Unreal
```

---

## How Complexity Is Estimated

The Orchestrator uses heuristics to estimate the number of output tokens needed:

### Building Count Estimation

```python
import re

def estimate_building_count(prompt: str) -> int:
    """Estimate how many buildings the user wants."""
    
    # Direct numbers: "40 buildings", "50 houses"
    match = re.search(r'(\d+)\s*(buildings?|houses?|structures?|towers?)', prompt, re.I)
    if match:
        return int(match.group(1))
    
    # Area descriptors
    area_keywords = {
        'village': 15,    'town': 30,     'city': 100,
        'block': 8,       'street': 10,   'neighborhood': 20,
        'district': 40,   'metropolis': 200
    }
    for keyword, count in area_keywords.items():
        if keyword in prompt.lower():
            return count
    
    # Detail multipliers
    detail_words = ['detailed', 'complex', 'varied', 'unique', 'diverse']
    detail_bonus = sum(1.3 for word in detail_words if word in prompt.lower())
    
    return 5  # Default: assume a small scene
```

### Token Budget Calculation

```python
TOKENS_PER_BUILDING = 200   # Average tokens for one building spec in JSON
OVERHEAD_TOKENS = 150        # JSON structure overhead (Intent, EnvironmentCheck, etc.)
SAFETY_MARGIN = 0.7          # Use only 70% of max to avoid truncation

def should_split(prompt: str, max_output_tokens: int) -> bool:
    count = estimate_building_count(prompt)
    estimated_tokens = (count * TOKENS_PER_BUILDING) + OVERHEAD_TOKENS
    budget = max_output_tokens * SAFETY_MARGIN
    return estimated_tokens > budget

def calculate_chunks(prompt: str, max_output_tokens: int) -> int:
    count = estimate_building_count(prompt)
    estimated_tokens = (count * TOKENS_PER_BUILDING) + OVERHEAD_TOKENS
    budget = max_output_tokens * SAFETY_MARGIN
    return max(1, math.ceil(estimated_tokens / budget))
```

---

## The Chunking Strategy

### Zone-Based Splitting

When the Orchestrator decides to split, it divides the scene into spatial zones:

```python
def generate_zone_prompts(original_prompt: str, num_chunks: int) -> list[str]:
    """Split a scene prompt into zone-specific sub-prompts."""
    
    count = estimate_building_count(original_prompt)
    per_chunk = math.ceil(count / num_chunks)
    
    zone_names = [
        "northern section",  "eastern section",
        "southern section",  "western section",
        "central area",      "outskirts"
    ]
    
    prompts = []
    for i in range(num_chunks):
        zone = zone_names[i % len(zone_names)]
        start = i * per_chunk
        end = min((i + 1) * per_chunk, count)
        actual_count = end - start
        
        sub_prompt = (
            f"You are generating part {i+1} of {num_chunks} of a larger scene.\n"
            f"Original request: {original_prompt}\n"
            f"Your task: Generate the {zone} with {actual_count} buildings.\n"
            f"Use IDs starting from 'Bldg_{start+1:03d}' to avoid conflicts.\n"
            f"Place buildings relative to the {zone} — offset coordinates appropriately.\n"
            f"Output a BatchSpawn JSON with exactly {actual_count} blueprints."
        )
        prompts.append(sub_prompt)
    
    return prompts
```

### Coordinate Partitioning

To prevent chunks from overlapping spatially, each zone gets a coordinate offset:

```
Chunk 1 (North):   Y offset = +3000 UU
Chunk 2 (Center):  Y offset = 0
Chunk 3 (South):   Y offset = -3000 UU
Chunk 4 (East):    X offset = +3000 UU
Chunk 5 (West):    X offset = -3000 UU
```

The LLM is instructed to place buildings relative to these offsets. Combined with C++'s auto-nudge, this prevents inter-chunk overlaps.

---

## Orchestrator Integration

### In Interactive Mode

```python
async def _run_builder_orchestrated(llm, prompt: str, max_tokens: int):
    if not should_split(prompt, max_tokens):
        # Simple case: one call is enough
        await _run_builder(llm, prompt)
        return
    
    num_chunks = calculate_chunks(prompt, max_tokens)
    zone_prompts = generate_zone_prompts(prompt, num_chunks)
    
    print(f"🧠 Complex scene detected — splitting into {num_chunks} generation passes.")
    
    all_receipts = []
    for i, sub_prompt in enumerate(zone_prompts):
        print(f"\n📦 Pass {i+1}/{num_chunks}...")
        result = await _run_builder(llm, sub_prompt)
        all_receipts.append(result)
    
    total_buildings = sum(
        len(json.loads(r).get("Results", [])) 
        for r in all_receipts if r
    )
    print(f"\n🏙️ Scene complete! {total_buildings} buildings placed across {num_chunks} passes.")
```

### CLI Flag

```bash
python agent.py gemini -b -i -o    # -o enables orchestrator
```

When `-o` is NOT set, the system works exactly as before (single-call mode). The orchestrator is opt-in to avoid unexpected behavior changes.

---

## Model-Specific Token Budgets

The Orchestrator knows the output capabilities of each supported backend:

```python
MODEL_TOKEN_BUDGETS = {
    "groq": 4096,       # Llama 3.3 70B via Groq
    "gemini": 8192,     # Gemini 2.5 Pro
    "ollama_default": 4096,  # Conservative default for local models
}
```

Users can override with `--max-tokens <N>` if they're using a custom model with different limits.

---

## The Token Efficiency Principle

The user's original directive was:

> *"As long as details given, as better the project. Let it create the best thing. Tokens must stay near max but still using them in different ways."*

This means each chunk should **maximize detail**, not minimize it. The Orchestrator doesn't just split evenly — it allocates the full token budget to each chunk:

- **Don't:** "Generate 14 buildings" (minimal prompt, wastes capacity)
- **Do:** "Generate 14 buildings for the northern district. Include variety: some should be 2-story wooden houses with pointed roofs, others should be stone shops with flat roofs. Vary the widths between 600-1200 UU. Space them along a road at Y=3000." (rich prompt that fills the budget)

The richer the sub-prompt, the more creative and detailed the LLM's output will be.

---

## Limitations

1. **Cross-chunk references:** The LLM generating chunk 2 doesn't know exactly where chunk 1's buildings ended up (after auto-nudge). Minor gaps or density variations may occur between zones.

2. **Style consistency:** Each LLM call is independent. The "western section" might use slightly different style choices than the "eastern section" unless the sub-prompt explicitly constrains this.

3. **Token estimation is heuristic:** A complex building with many custom parameters takes more tokens than a simple one. The 200-token estimate is an average that works well in practice but isn't exact.

4. **Sequential processing:** Chunks are sent to Unreal one at a time. A 5-chunk city takes ~5x longer than a single-chunk scene. This is acceptable because the per-chunk building time is fast (C++ HISM is instant).

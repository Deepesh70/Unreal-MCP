import asyncio
from agents.pipeline import two_phase_run
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv() # This pulls the key from your .env file into Python's memory

async def test_self_healing():
    # 1. Initialize your LLM (Ensure your GROQ_API_KEY is in .env)
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)

    print("\n" + "="*60)
    print("  STRESS TEST: THE SELF-HEALING FIREWALL")
    print("="*60)

    # 2. We give it a prompt that often causes C++ syntax hallucinations
    # specifically asking for complex pointer math or TArrays
    broken_prompt = (
        "Create a 'DamageZone' actor that has a TArray of all overlapping actors. "
        "In the Tick function, loop through the array and call a function 'ApplyInternalDamage' "
        "on them, but deliberately forget to check if the pointers are null."
    )

    print(f"\n[STEP 1] Feeding 'Dangerous' Prompt: \n{broken_prompt}")
    
    try:
        # Run the pipeline. This will:
        # - Generate the C++
        # - Write to disk
        # - Trigger run_headless_compile_check()
        # - Catch the 'nullptr' or 'syntax' error
        # - Feed it back to the LLM for Attempt #2
        result = await two_phase_run(llm, broken_prompt, write_files=True)
        
        print(f"\n[FINAL RESULT] {result}")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] The pipeline itself crashed: {e}")

if __name__ == "__main__":
    asyncio.run(test_self_healing())
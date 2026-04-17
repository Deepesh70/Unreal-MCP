import os
import re

# --- CONFIGURATION ---
# Target your specific UE 5.6 installation path.
UE_CLASSES_DIR = r"E:\Unreal Engine\UE_5.6\Engine\Source\Runtime\Engine\Classes"
OUTPUT_FILE = "data/ue_api_knowledge.md"

# Regex to find: class ENGINE_API UBoxComponent : public UShapeComponent
# CLASS_PATTERN = re.compile(r"class\s+[A-Z_]*API\s+(U[a-zA-Z0-9_]+Component)\s*:")
CLASS_PATTERN = re.compile(r"class\s+(?:[A-Z_]+API\s+)?(U[a-zA-Z0-9_]+Component)[^:{]*:")
def crawl_unreal_components(source_dir: str, output_file: str):
    if not os.path.exists(source_dir):
        print(f"[!] FATAL: Unreal Engine source path not found at: {source_dir}")
        return

    print(f"[*] Crawling UE5 Source for Components at: {source_dir}")
    knowledge_blocks = []
    processed_classes = set()

    for root, _, files in os.walk(source_dir):
        for file in files:
            if not file.endswith("Component.h"):
                continue

            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                if "UCLASS(" not in content:
                    continue

                match = CLASS_PATTERN.search(content)
                if match:
                    class_name = match.group(1)
                    if class_name in processed_classes:
                        continue
                    processed_classes.add(class_name)

                    # Calculate relative include path
                    relative_path = os.path.relpath(filepath, start=source_dir)
                    include_path = relative_path.replace("\\", "/")

                    block = f"## {class_name}\n"
                    block += f"Include: \"{include_path}\"\n"
                    
                    stripped_name = class_name.replace('U', '', 1)
                    block += f"Constructor: CreateDefaultSubobject<{class_name}>(TEXT(\"{stripped_name}\"))\n"
                    block += f"Pointer Rules: {class_name}*. Always use asterisk.\n"
                    
                    if class_name == "UStaticMeshComponent":
                        block += "Include2: \"UObject/ConstructorHelpers.h\"\n"
                        block += "Instantiation: SetupAttachment(RootComponent) if it's a visual mesh.\n"
                        block += "Asset Injection: To assign a default shape, use: static ConstructorHelpers::FObjectFinder<UStaticMesh> MeshAsset(TEXT(\"StaticMesh'/Engine/BasicShapes/Cube.Cube'\")); if(MeshAsset.Succeeded()){ Mesh->SetStaticMesh(MeshAsset.Object); }\n"
                    else:
                        block += "Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.\n"

                    knowledge_blocks.append(block)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Unreal Engine 5 Auto-Generated C++ API Ground Truth\n\n")
        f.write("\n\n".join(knowledge_blocks))

    print(f"[+] Success: Scraped {len(knowledge_blocks)} UE5 Components.")
    print(f"[+] Output saved to: {output_file}")

if __name__ == "__main__":
    crawl_unreal_components(UE_CLASSES_DIR, OUTPUT_FILE)

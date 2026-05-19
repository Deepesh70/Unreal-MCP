// ProceduralBaseActor.cpp

#include "ProceduralBaseActor.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonReader.h"
#include "UObject/ConstructorHelpers.h"

AProceduralBaseActor::AProceduralBaseActor()
{
    PrimaryActorTick.bCanEverTick = false;
}

UHierarchicalInstancedStaticMeshComponent* AProceduralBaseActor::GetOrCreateHISM(UStaticMesh* Mesh, UMaterialInterface* Material)
{
    if (!Mesh) return nullptr;

    FHISMPoolKey Key;
    Key.Mesh = Mesh;
    Key.Material = Material;

    if (auto* Found = HISMPool.Find(Key))
    {
        return *Found;
    }

    FName ComponentName = MakeUniqueObjectName(this, UHierarchicalInstancedStaticMeshComponent::StaticClass(), TEXT("HISM_Comp"));
    auto* NewHISM = NewObject<UHierarchicalInstancedStaticMeshComponent>(this, ComponentName);
    NewHISM->SetStaticMesh(Mesh);
    
    if (Material)
    {
        for (int32 i = 0; i < Mesh->GetStaticMaterials().Num(); ++i)
        {
            NewHISM->SetMaterial(i, Material);
        }
    }

    if (!GetRootComponent())
    {
        SetRootComponent(NewHISM);
    }
    else
    {
        NewHISM->SetupAttachment(GetRootComponent());
    }
    NewHISM->RegisterComponent();

    HISMPool.Add(Key, NewHISM);
    return NewHISM;
}

bool AProceduralBaseActor::HandleInstancedSpawn(const FString& AssetPath, const FString& TransformsJson)
{
    UStaticMesh* Mesh = Cast<UStaticMesh>(StaticLoadObject(UStaticMesh::StaticClass(), nullptr, *AssetPath));
    if (!Mesh)
    {
        UE_LOG(LogTemp, Error, TEXT("AProceduralBaseActor::HandleInstancedSpawn - Could not load mesh: %s"), *AssetPath);
        return false;
    }

    UHierarchicalInstancedStaticMeshComponent* HISM = GetOrCreateHISM(Mesh, nullptr);
    if (!HISM) return false;

    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(TransformsJson);
    TArray<TSharedPtr<FJsonValue>> TransformsArray;

    if (!FJsonSerializer::Deserialize(Reader, TransformsArray))
    {
        UE_LOG(LogTemp, Error, TEXT("AProceduralBaseActor::HandleInstancedSpawn - Failed to parse TransformsJson"));
        return false;
    }

    for (const auto& Val : TransformsArray)
    {
        const TSharedPtr<FJsonObject>* Obj;
        if (Val->TryGetObject(Obj) && (*Obj).IsValid())
        {
            FVector Loc = FVector::ZeroVector;
            FRotator Rot = FRotator::ZeroRotator;
            FVector Scale = FVector::OneVector;

            const TArray<TSharedPtr<FJsonValue>>* LocArr;
            if ((*Obj)->TryGetArrayField(TEXT("Loc"), LocArr) && LocArr->Num() >= 3)
            {
                Loc = FVector((*LocArr)[0]->AsNumber(), (*LocArr)[1]->AsNumber(), (*LocArr)[2]->AsNumber());
            }

            const TArray<TSharedPtr<FJsonValue>>* RotArr;
            if ((*Obj)->TryGetArrayField(TEXT("Rot"), RotArr) && RotArr->Num() >= 3)
            {
                Rot = FRotator((*RotArr)[0]->AsNumber(), (*RotArr)[1]->AsNumber(), (*RotArr)[2]->AsNumber());
            }

            const TArray<TSharedPtr<FJsonValue>>* ScaleArr;
            if ((*Obj)->TryGetArrayField(TEXT("Scale"), ScaleArr) && ScaleArr->Num() >= 3)
            {
                Scale = FVector((*ScaleArr)[0]->AsNumber(), (*ScaleArr)[1]->AsNumber(), (*ScaleArr)[2]->AsNumber());
            }

            FTransform Transform(Rot, Loc, Scale);
            HISM->AddInstance(Transform, true); // true to defer render update for bulk spawn
        }
    }

    // Force an update after bulk spawning
    HISM->MarkRenderStateDirty();

    return true;
}

#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "FreezeTrap.generated.h"

UCLASS(Blueprintable, Placeable)
class YOURPROJECT_API AFreezeTrap : public AActor
{
    GENERATED_BODY()

public: 
    AFreezeTrap();

protected:
    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

public: 
    // Called every frame
    virtual void Tick(float DeltaTime) override;

};
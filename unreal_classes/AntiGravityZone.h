#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/BoxComponent.h"
#include "AntiGravityZone.generated.h"

UCLASS()
class YOURPROJECTNAME_API AAntiGravityZone : public AActor
{
    GENERATED_BODY()
    
public:    
    AAntiGravityZone();

protected:
    virtual void BeginPlay() override;

public:    
    // The invisible box that triggers the gravity effect
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    UBoxComponent* CollisionBox;

    // How fast objects float upwards
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gravity Settings")
    float UpwardForce;

    // Overlap events
    UFUNCTION()
    void OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

    UFUNCTION()
    void OnOverlapEnd(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);
};

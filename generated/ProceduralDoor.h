#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/StaticMeshComponent.h"
#include "ProceduralDoor.generated.h"

UCLASS()
class {{PROJECT_API}} AProceduralDoor : public AActor
{
	GENERATED_BODY()
	
public:	
	AProceduralDoor();

protected:
	virtual void BeginPlay() override;

public:	
	virtual void Tick(float DeltaTime) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* DoorMesh;

	UFUNCTION(BlueprintCallable, Category = "Procedural")
	void ToggleDoor();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural")
	bool bIsOpen = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural")
	float OpenRotation = 90.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural")
	float AnimationSpeed = 5.0f;

private:
	float CurrentRotation = 0.0f;
	float TargetRotation = 0.0f;
};

#include "ProceduralDoor.h"
#include "UObject/ConstructorHelpers.h"

AProceduralDoor::AProceduralDoor()
{
	PrimaryActorTick.bCanEverTick = true;

	DoorMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DoorMesh"));
	RootComponent = DoorMesh;

	// Use a standard cube mesh for the door, scaled later
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube"));
	if (CubeMesh.Succeeded())
	{
		DoorMesh->SetStaticMesh(CubeMesh.Object);
	}
}

void AProceduralDoor::BeginPlay()
{
	Super::BeginPlay();
	CurrentRotation = GetActorRotation().Yaw;
	TargetRotation = CurrentRotation;
}

void AProceduralDoor::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// Smoothly interpolate to target rotation
	if (FMath::Abs(CurrentRotation - TargetRotation) > 0.1f)
	{
		CurrentRotation = FMath::FInterpTo(CurrentRotation, TargetRotation, DeltaTime, AnimationSpeed);
		FRotator NewRot = GetActorRotation();
		NewRot.Yaw = CurrentRotation;
		SetActorRotation(NewRot);
	}
}

void AProceduralDoor::ToggleDoor()
{
	bIsOpen = !bIsOpen;
	
	// Assuming initial rotation is 0, we rotate by OpenRotation
	if (bIsOpen)
	{
		TargetRotation += OpenRotation;
	}
	else
	{
		TargetRotation -= OpenRotation;
	}
}

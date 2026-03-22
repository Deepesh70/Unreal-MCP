#include "AntiGravityZone.h"

AAntiGravityZone::AAntiGravityZone()
{
    PrimaryActorTick.bCanEverTick = false;

    // Setup the collision box
    CollisionBox = CreateDefaultSubobject<UBoxComponent>(TEXT("CollisionBox"));
    RootComponent = CollisionBox;
    CollisionBox->SetBoxExtent(FVector(500.f, 500.f, 500.f)); // Default size

    UpwardForce = 500.0f;

    // Bind the overlap events
    CollisionBox->OnComponentBeginOverlap.AddDynamic(this, &AAntiGravityZone::OnOverlapBegin);
    CollisionBox->OnComponentEndOverlap.AddDynamic(this, &AAntiGravityZone::OnOverlapEnd);
}

void AAntiGravityZone::BeginPlay()
{
    Super::BeginPlay();
}

void AAntiGravityZone::OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    // If the object entering the box uses physics, make it float
    if (OtherComp && OtherComp->IsSimulatingPhysics())
    {
        OtherComp->SetEnableGravity(false);
        OtherComp->AddForce(FVector(0.f, 0.f, UpwardForce), NAME_None, true);
    }
}

void AAntiGravityZone::OnOverlapEnd(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex)
{
    // Restore normal gravity when it leaves the box
    if (OtherComp && OtherComp->IsSimulatingPhysics())
    {
        OtherComp->SetEnableGravity(true);
    }
}

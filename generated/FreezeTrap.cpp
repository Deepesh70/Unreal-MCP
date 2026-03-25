#include "FreezeTrap.h"

AFreezeTrap::AFreezeTrap()
{
    // Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
    PrimaryActorTick.bCanEverTick = true;
}

void AFreezeTrap::BeginPlay()
{
    Super::BeginPlay();

    // Put your initialization code here
}

void AFreezeTrap::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    // Put your tick code here
}

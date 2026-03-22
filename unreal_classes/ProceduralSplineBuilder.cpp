#include "ProceduralSplineBuilder.h"
#include "Components/SplineMeshComponent.h"

AProceduralSplineBuilder::AProceduralSplineBuilder()
{
    PrimaryActorTick.bCanEverTick = false;

    PathSpline = CreateDefaultSubobject<USplineComponent>(TEXT("PathSpline"));
    RootComponent = PathSpline;
}

// This function takes the simple array of coordinates from your AI
void AProceduralSplineBuilder::BuildPathFromCoordinates(const TArray<FVector>& Points)
{
    PathSpline->ClearSplinePoints();

    for (const FVector& Point : Points)
    {
        PathSpline->AddSplinePoint(Point, ESplineCoordinateSpace::Local, true);
    }
    
    // Trigger the construction script to build the meshes
    OnConstruction(GetTransform());
}

// This automatically stretches the meshes along the curve
void AProceduralSplineBuilder::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);

    if (!MeshToUse) return;

    int32 NumPoints = PathSpline->GetNumberOfSplinePoints();

    for (int32 i = 0; i < NumPoints - 1; i++)
    {
        USplineMeshComponent* SplineMesh = NewObject<USplineMeshComponent>(this);
        SplineMesh->SetStaticMesh(MeshToUse);
        SplineMesh->SetForwardAxis(ESplineMeshAxis::X);
        SplineMesh->SetMobility(EComponentMobility::Movable);
        SplineMesh->CreationMethod = EComponentCreationMethod::UserConstructionScript;
        SplineMesh->RegisterComponentWithWorld(GetWorld());

        FVector StartPos, StartTangent, EndPos, EndTangent;
        PathSpline->GetLocationAndTangentAtSplinePoint(i, StartPos, StartTangent, ESplineCoordinateSpace::Local);
        PathSpline->GetLocationAndTangentAtSplinePoint(i + 1, EndPos, EndTangent, ESplineCoordinateSpace::Local);

        SplineMesh->SetStartAndEnd(StartPos, StartTangent, EndPos, EndTangent, true);
    }
}

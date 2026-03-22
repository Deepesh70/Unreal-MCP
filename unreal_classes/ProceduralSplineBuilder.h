#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/SplineComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "ProceduralSplineBuilder.generated.h"

UCLASS()
class YOURPROJECTNAME_API AProceduralSplineBuilder : public AActor
{
    GENERATED_BODY()
    
public:    
    AProceduralSplineBuilder();

protected:
    virtual void OnConstruction(const FTransform& Transform) override;

public:    
    // The mathematical path
    UPROPERTY(VisibleAnywhere, Category = "Spline")
    USplineComponent* PathSpline;

    // The mesh to stretch along the path (e.g., a brick wall)
    UPROPERTY(EditAnywhere, Category = "Spline")
    UStaticMesh* MeshToUse;

    // Call this from Python/JSON to feed it coordinates
    UFUNCTION(BlueprintCallable, Category = "Spline")
    void BuildPathFromCoordinates(const TArray<FVector>& Points);
};

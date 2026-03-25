// Copyright 2023 Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Components/BoxComponent.h"

class YOURPROJECT_API AAntiGravityZone : public AActor
{
GENERATED_BODY()

public:

    // Sets default values for this actor's properties
    AAntiGravityZone();

    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

    // Called every frame
    virtual void Tick(float DeltaTime) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Settings")
    float GravityStrength;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Settings")
    float ZoneRadius;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Settings")
    bool bEnableGravity;

    UBoxComponent* GravityZoneBox;

public:

    // Called to bind functionality to input
    virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26, bool bRenderInScreenSpace27) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26, bool bRenderInScreenSpace27, bool bRenderInScreenSpace28) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26, bool bRenderInScreenSpace27, bool bRenderInScreenSpace28, bool bRenderInScreenSpace29) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26, bool bRenderInScreenSpace27, bool bRenderInScreenSpace28, bool bRenderInScreenSpace29, bool bRenderInScreenSpace30) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26, bool bRenderInScreenSpace27, bool bRenderInScreenSpace28, bool bRenderInScreenSpace29, bool bRenderInScreenSpace30, bool bRenderInScreenSpace31) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26, bool bRenderInScreenSpace27, bool bRenderInScreenSpace28, bool bRenderInScreenSpace29, bool bRenderInScreenSpace30, bool bRenderInScreenSpace31, bool bRenderInScreenSpace32) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26, bool bRenderInScreenSpace27, bool bRenderInScreenSpace28, bool bRenderInScreenSpace29, bool bRenderInScreenSpace30, bool bRenderInScreenSpace31, bool bRenderInScreenSpace32, bool bRenderInScreenSpace33) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26, bool bRenderInScreenSpace27, bool bRenderInScreenSpace28, bool bRenderInScreenSpace29, bool bRenderInScreenSpace30, bool bRenderInScreenSpace31, bool bRenderInScreenSpace32, bool bRenderInScreenSpace33, bool bRenderInScreenSpace34) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26, bool bRenderInScreenSpace27, bool bRenderInScreenSpace28, bool bRenderInScreenSpace29, bool bRenderInScreenSpace30, bool bRenderInScreenSpace31, bool bRenderInScreenSpace32, bool bRenderInScreenSpace33, bool bRenderInScreenSpace34, bool bRenderInScreenSpace35) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26, bool bRenderInScreenSpace27, bool bRenderInScreenSpace28, bool bRenderInScreenSpace29, bool bRenderInScreenSpace30, bool bRenderInScreenSpace31, bool bRenderInScreenSpace32, bool bRenderInScreenSpace33, bool bRenderInScreenSpace34, bool bRenderInScreenSpace35, bool bRenderInScreenSpace36) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26, bool bRenderInScreenSpace27, bool bRenderInScreenSpace28, bool bRenderInScreenSpace29, bool bRenderInScreenSpace30, bool bRenderInScreenSpace31, bool bRenderInScreenSpace32, bool bRenderInScreenSpace33, bool bRenderInScreenSpace34, bool bRenderInScreenSpace35, bool bRenderInScreenSpace36, bool bRenderInScreenSpace37) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRenderInScreenSpace23, bool bRenderInScreenSpace24, bool bRenderInScreenSpace25, bool bRenderInScreenSpace26, bool bRenderInScreenSpace27, bool bRenderInScreenSpace28, bool bRenderInScreenSpace29, bool bRenderInScreenSpace30, bool bRenderInScreenSpace31, bool bRenderInScreenSpace32, bool bRenderInScreenSpace33, bool bRenderInScreenSpace34, bool bRenderInScreenSpace35, bool bRenderInScreenSpace36, bool bRenderInScreenSpace37, bool bRenderInScreenSpace38) override;

    // Called to draw the component
    virtual void DrawComponent(float DeltaTime, class UCanvas* Canvas, FViewport* Viewport, FSceneView* View, FActorComponentRange VisibilityRect, bool bRenderInScreenSpace, bool bRenderInScreenSpace2, bool bRenderInScreenSpace3, bool bRenderInScreenSpace4, bool bRenderInScreenSpace5, bool bRenderInScreenSpace6, bool bRenderInScreenSpace7, bool bRenderInScreenSpace8, bool bRenderInScreenSpace9, bool bRenderInScreenSpace10, bool bRenderInScreenSpace11, bool bRenderInScreenSpace12, bool bRenderInScreenSpace13, bool bRenderInScreenSpace14, bool bRenderInScreenSpace15, bool bRenderInScreenSpace16, bool bRenderInScreenSpace17, bool bRenderInScreenSpace18, bool bRenderInScreenSpace19, bool bRenderInScreenSpace20, bool bRenderInScreenSpace21, bool bRenderInScreenSpace22, bool bRender
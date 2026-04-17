# Unreal Engine 5 Auto-Generated C++ API Ground Truth

## Actor Base Construction Rules
Rule 1: Every physical Actor MUST have a `USceneComponent` created and assigned as the `RootComponent` in the constructor.
Rule 2: Never assign default values to `TArray` properties in the header file (e.g., do NOT write `TArray<FString> Arr = {"A"}`). Leave them unassigned.
Rule 3: If the user asks for a physical object (like a building, weapon, or prop), you MUST declare and instantiate at least one `UStaticMeshComponent` and attach it to the `RootComponent`.

## UCameraProxyMeshComponent
Include: "Camera/CameraComponent.h"
Constructor: CreateDefaultSubobject<UCameraProxyMeshComponent>(TEXT("CameraProxyMeshComponent"))
Pointer Rules: UCameraProxyMeshComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UCameraShakeSourceComponent
Include: "Camera/CameraShakeSourceComponent.h"
Constructor: CreateDefaultSubobject<UCameraShakeSourceComponent>(TEXT("CameraShakeSourceComponent"))
Pointer Rules: UCameraShakeSourceComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UActorComponent
Include: "Components/ActorComponent.h"
Constructor: CreateDefaultSubobject<UActorComponent>(TEXT("ActorComponent"))
Pointer Rules: UActorComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UApplicationLifecycleComponent
Include: "Components/ApplicationLifecycleComponent.h"
Constructor: CreateDefaultSubobject<UApplicationLifecycleComponent>(TEXT("ApplicationLifecycleComponent"))
Pointer Rules: UApplicationLifecycleComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UArrowComponent
Include: "Components/ArrowComponent.h"
Constructor: CreateDefaultSubobject<UArrowComponent>(TEXT("ArrowComponent"))
Pointer Rules: UArrowComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UAudioComponent
Include: "Components/AudioComponent.h"
Constructor: CreateDefaultSubobject<UAudioComponent>(TEXT("AudioComponent"))
Pointer Rules: UAudioComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UBillboardComponent
Include: "Components/BillboardComponent.h"
Constructor: CreateDefaultSubobject<UBillboardComponent>(TEXT("BillboardComponent"))
Pointer Rules: UBillboardComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UBoundsCopyComponent
Include: "Components/BoundsCopyComponent.h"
Constructor: CreateDefaultSubobject<UBoundsCopyComponent>(TEXT("BoundsCopyComponent"))
Pointer Rules: UBoundsCopyComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UBoxComponent
Include: "Components/BoxComponent.h"
Constructor: CreateDefaultSubobject<UBoxComponent>(TEXT("BoxComponent"))
Pointer Rules: UBoxComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UBoxReflectionCaptureComponent
Include: "Components/BoxReflectionCaptureComponent.h"
Constructor: CreateDefaultSubobject<UBoxReflectionCaptureComponent>(TEXT("BoxReflectionCaptureComponent"))
Pointer Rules: UBoxReflectionCaptureComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UBrushComponent
Include: "Components/BrushComponent.h"
Constructor: CreateDefaultSubobject<UBrushComponent>(TEXT("BrushComponent"))
Pointer Rules: UBrushComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UCapsuleComponent
Include: "Components/CapsuleComponent.h"
Constructor: CreateDefaultSubobject<UCapsuleComponent>(TEXT("CapsuleComponent"))
Pointer Rules: UCapsuleComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UChildActorComponent
Include: "Components/ChildActorComponent.h"
Constructor: CreateDefaultSubobject<UChildActorComponent>(TEXT("ChildActorComponent"))
Pointer Rules: UChildActorComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UDecalComponent
Include: "Components/DecalComponent.h"
Constructor: CreateDefaultSubobject<UDecalComponent>(TEXT("DecalComponent"))
Pointer Rules: UDecalComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UDirectionalLightComponent
Include: "Components/DirectionalLightComponent.h"
Constructor: CreateDefaultSubobject<UDirectionalLightComponent>(TEXT("DirectionalLightComponent"))
Pointer Rules: UDirectionalLightComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UDrawFrustumComponent
Include: "Components/DrawFrustumComponent.h"
Constructor: CreateDefaultSubobject<UDrawFrustumComponent>(TEXT("DrawFrustumComponent"))
Pointer Rules: UDrawFrustumComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UDrawSphereComponent
Include: "Components/DrawSphereComponent.h"
Constructor: CreateDefaultSubobject<UDrawSphereComponent>(TEXT("DrawSphereComponent"))
Pointer Rules: UDrawSphereComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UExponentialHeightFogComponent
Include: "Components/ExponentialHeightFogComponent.h"
Constructor: CreateDefaultSubobject<UExponentialHeightFogComponent>(TEXT("ExponentialHeightFogComponent"))
Pointer Rules: UExponentialHeightFogComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UForceFeedbackComponent
Include: "Components/ForceFeedbackComponent.h"
Constructor: CreateDefaultSubobject<UForceFeedbackComponent>(TEXT("ForceFeedbackComponent"))
Pointer Rules: UForceFeedbackComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UHeterogeneousVolumeComponent
Include: "Components/HeterogeneousVolumeComponent.h"
Constructor: CreateDefaultSubobject<UHeterogeneousVolumeComponent>(TEXT("HeterogeneousVolumeComponent"))
Pointer Rules: UHeterogeneousVolumeComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UHierarchicalInstancedStaticMeshComponent
Include: "Components/HierarchicalInstancedStaticMeshComponent.h"
Constructor: CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("HierarchicalInstancedStaticMeshComponent"))
Pointer Rules: UHierarchicalInstancedStaticMeshComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UInputComponent
Include: "Components/InputComponent.h"
Constructor: CreateDefaultSubobject<UInputComponent>(TEXT("InputComponent"))
Pointer Rules: UInputComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UInstancedSkinnedMeshComponent
Include: "Components/InstancedSkinnedMeshComponent.h"
Constructor: CreateDefaultSubobject<UInstancedSkinnedMeshComponent>(TEXT("InstancedSkinnedMeshComponent"))
Pointer Rules: UInstancedSkinnedMeshComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UInstancedStaticMeshComponent
Include: "Components/InstancedStaticMeshComponent.h"
Constructor: CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("InstancedStaticMeshComponent"))
Pointer Rules: UInstancedStaticMeshComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UInterpToMovementComponent
Include: "Components/InterpToMovementComponent.h"
Constructor: CreateDefaultSubobject<UInterpToMovementComponent>(TEXT("InterpToMovementComponent"))
Pointer Rules: UInterpToMovementComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UPrimitiveComponent
Include: "Components/LightComponent.h"
Constructor: CreateDefaultSubobject<UPrimitiveComponent>(TEXT("PrimitiveComponent"))
Pointer Rules: UPrimitiveComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## ULightmassPortalComponent
Include: "Components/LightmassPortalComponent.h"
Constructor: CreateDefaultSubobject<ULightmassPortalComponent>(TEXT("LightmassPortalComponent"))
Pointer Rules: ULightmassPortalComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## ULineBatchComponent
Include: "Components/LineBatchComponent.h"
Constructor: CreateDefaultSubobject<ULineBatchComponent>(TEXT("LineBatchComponent"))
Pointer Rules: ULineBatchComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## ULocalFogVolumeComponent
Include: "Components/LocalFogVolumeComponent.h"
Constructor: CreateDefaultSubobject<ULocalFogVolumeComponent>(TEXT("LocalFogVolumeComponent"))
Pointer Rules: ULocalFogVolumeComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## ULocalLightComponent
Include: "Components/LocalLightComponent.h"
Constructor: CreateDefaultSubobject<ULocalLightComponent>(TEXT("LocalLightComponent"))
Pointer Rules: ULocalLightComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## ULODSyncComponent
Include: "Components/LODSyncComponent.h"
Constructor: CreateDefaultSubobject<ULODSyncComponent>(TEXT("LODSyncComponent"))
Pointer Rules: ULODSyncComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UMaterialBillboardComponent
Include: "Components/MaterialBillboardComponent.h"
Constructor: CreateDefaultSubobject<UMaterialBillboardComponent>(TEXT("MaterialBillboardComponent"))
Pointer Rules: UMaterialBillboardComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UMeshComponent
Include: "Components/MeshComponent.h"
Constructor: CreateDefaultSubobject<UMeshComponent>(TEXT("MeshComponent"))
Pointer Rules: UMeshComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## ULightComponent
Include: "Components/ModelComponent.h"
Constructor: CreateDefaultSubobject<ULightComponent>(TEXT("LightComponent"))
Pointer Rules: ULightComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UPawnNoiseEmitterComponent
Include: "Components/PawnNoiseEmitterComponent.h"
Constructor: CreateDefaultSubobject<UPawnNoiseEmitterComponent>(TEXT("PawnNoiseEmitterComponent"))
Pointer Rules: UPawnNoiseEmitterComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UPlanarReflectionComponent
Include: "Components/PlanarReflectionComponent.h"
Constructor: CreateDefaultSubobject<UPlanarReflectionComponent>(TEXT("PlanarReflectionComponent"))
Pointer Rules: UPlanarReflectionComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UPlaneReflectionCaptureComponent
Include: "Components/PlaneReflectionCaptureComponent.h"
Constructor: CreateDefaultSubobject<UPlaneReflectionCaptureComponent>(TEXT("PlaneReflectionCaptureComponent"))
Pointer Rules: UPlaneReflectionCaptureComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UPlatformEventsComponent
Include: "Components/PlatformEventsComponent.h"
Constructor: CreateDefaultSubobject<UPlatformEventsComponent>(TEXT("PlatformEventsComponent"))
Pointer Rules: UPlatformEventsComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UPointLightComponent
Include: "Components/PointLightComponent.h"
Constructor: CreateDefaultSubobject<UPointLightComponent>(TEXT("PointLightComponent"))
Pointer Rules: UPointLightComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## USkeletalMeshComponent
Include: "Components/PoseableMeshComponent.h"
Constructor: CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("SkeletalMeshComponent"))
Pointer Rules: USkeletalMeshComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UPostProcessComponent
Include: "Components/PostProcessComponent.h"
Constructor: CreateDefaultSubobject<UPostProcessComponent>(TEXT("PostProcessComponent"))
Pointer Rules: UPostProcessComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## URectLightComponent
Include: "Components/RectLightComponent.h"
Constructor: CreateDefaultSubobject<URectLightComponent>(TEXT("RectLightComponent"))
Pointer Rules: URectLightComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## URuntimeVirtualTextureComponent
Include: "Components/RuntimeVirtualTextureComponent.h"
Constructor: CreateDefaultSubobject<URuntimeVirtualTextureComponent>(TEXT("RuntimeVirtualTextureComponent"))
Pointer Rules: URuntimeVirtualTextureComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## USceneComponent
Include: "Components/SceneComponent.h"
Constructor: CreateDefaultSubobject<USceneComponent>(TEXT("SceneComponent"))
Pointer Rules: USceneComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UShapeComponent
Include: "Components/ShapeComponent.h"
Constructor: CreateDefaultSubobject<UShapeComponent>(TEXT("ShapeComponent"))
Pointer Rules: UShapeComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## USkinnedMeshComponent
Include: "Components/SkinnedMeshComponent.h"
Constructor: CreateDefaultSubobject<USkinnedMeshComponent>(TEXT("SkinnedMeshComponent"))
Pointer Rules: USkinnedMeshComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## USkyAtmosphereComponent
Include: "Components/SkyAtmosphereComponent.h"
Constructor: CreateDefaultSubobject<USkyAtmosphereComponent>(TEXT("SkyAtmosphereComponent"))
Pointer Rules: USkyAtmosphereComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## USkyLightComponent
Include: "Components/SkyLightComponent.h"
Constructor: CreateDefaultSubobject<USkyLightComponent>(TEXT("SkyLightComponent"))
Pointer Rules: USkyLightComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## USphereComponent
Include: "Components/SphereComponent.h"
Constructor: CreateDefaultSubobject<USphereComponent>(TEXT("SphereComponent"))
Pointer Rules: USphereComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## USphereReflectionCaptureComponent
Include: "Components/SphereReflectionCaptureComponent.h"
Constructor: CreateDefaultSubobject<USphereReflectionCaptureComponent>(TEXT("SphereReflectionCaptureComponent"))
Pointer Rules: USphereReflectionCaptureComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## USplineComponent
Include: "Components/SplineComponent.h"
Constructor: CreateDefaultSubobject<USplineComponent>(TEXT("SplineComponent"))
Pointer Rules: USplineComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## USplineMeshComponent
Include: "Components/SplineMeshComponent.h"
Constructor: CreateDefaultSubobject<USplineMeshComponent>(TEXT("SplineMeshComponent"))
Pointer Rules: USplineMeshComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## USpotLightComponent
Include: "Components/SpotLightComponent.h"
Constructor: CreateDefaultSubobject<USpotLightComponent>(TEXT("SpotLightComponent"))
Pointer Rules: USpotLightComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UStaticMeshComponent
Include: "Components/StaticMeshComponent.h"
Constructor: CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StaticMeshComponent"))
Pointer Rules: UStaticMeshComponent*. Always use asterisk.
Include2: "UObject/ConstructorHelpers.h"
Instantiation: SetupAttachment(RootComponent) if it's a visual mesh.
Asset Injection: To assign a default shape, use: static ConstructorHelpers::FObjectFinder<UStaticMesh> MeshAsset(TEXT("StaticMesh'/Engine/BasicShapes/Cube.Cube'")); if(MeshAsset.Succeeded()){ Mesh->SetStaticMesh(MeshAsset.Object); }


## UStereoLayerComponent
Include: "Components/StereoLayerComponent.h"
Constructor: CreateDefaultSubobject<UStereoLayerComponent>(TEXT("StereoLayerComponent"))
Pointer Rules: UStereoLayerComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UTextRenderComponent
Include: "Components/TextRenderComponent.h"
Constructor: CreateDefaultSubobject<UTextRenderComponent>(TEXT("TextRenderComponent"))
Pointer Rules: UTextRenderComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UTimelineComponent
Include: "Components/TimelineComponent.h"
Constructor: CreateDefaultSubobject<UTimelineComponent>(TEXT("TimelineComponent"))
Pointer Rules: UTimelineComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UVectorFieldComponent
Include: "Components/VectorFieldComponent.h"
Constructor: CreateDefaultSubobject<UVectorFieldComponent>(TEXT("VectorFieldComponent"))
Pointer Rules: UVectorFieldComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UVolumetricCloudComponent
Include: "Components/VolumetricCloudComponent.h"
Constructor: CreateDefaultSubobject<UVolumetricCloudComponent>(TEXT("VolumetricCloudComponent"))
Pointer Rules: UVolumetricCloudComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UWindDirectionalSourceComponent
Include: "Components/WindDirectionalSourceComponent.h"
Constructor: CreateDefaultSubobject<UWindDirectionalSourceComponent>(TEXT("WindDirectionalSourceComponent"))
Pointer Rules: UWindDirectionalSourceComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UWorldPartitionStreamingSourceComponent
Include: "Components/WorldPartitionStreamingSourceComponent.h"
Constructor: CreateDefaultSubobject<UWorldPartitionStreamingSourceComponent>(TEXT("WorldPartitionStreamingSourceComponent"))
Pointer Rules: UWorldPartitionStreamingSourceComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UDebugDrawComponent
Include: "Debug/DebugDrawComponent.h"
Constructor: CreateDefaultSubobject<UDebugDrawComponent>(TEXT("DebugDrawComponent"))
Pointer Rules: UDebugDrawComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UCharacterMovementComponent
Include: "GameFramework/CharacterMovementComponent.h"
Constructor: CreateDefaultSubobject<UCharacterMovementComponent>(TEXT("CharacterMovementComponent"))
Pointer Rules: UCharacterMovementComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UMovementComponent
Include: "GameFramework/MovementComponent.h"
Constructor: CreateDefaultSubobject<UMovementComponent>(TEXT("MovementComponent"))
Pointer Rules: UMovementComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UProjectileMovementComponent
Include: "GameFramework/ProjectileMovementComponent.h"
Constructor: CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("ProjectileMovementComponent"))
Pointer Rules: UProjectileMovementComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## URotatingMovementComponent
Include: "GameFramework/RotatingMovementComponent.h"
Constructor: CreateDefaultSubobject<URotatingMovementComponent>(TEXT("RotatingMovementComponent"))
Pointer Rules: URotatingMovementComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## USpringArmComponent
Include: "GameFramework/SpringArmComponent.h"
Constructor: CreateDefaultSubobject<USpringArmComponent>(TEXT("SpringArmComponent"))
Pointer Rules: USpringArmComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UFXSystemComponent
Include: "Particles/ParticleSystemComponent.h"
Constructor: CreateDefaultSubobject<UFXSystemComponent>(TEXT("FXSystemComponent"))
Pointer Rules: UFXSystemComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UClusterUnionComponent
Include: "PhysicsEngine/ClusterUnionComponent.h"
Constructor: CreateDefaultSubobject<UClusterUnionComponent>(TEXT("ClusterUnionComponent"))
Pointer Rules: UClusterUnionComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UPhysicalAnimationComponent
Include: "PhysicsEngine/PhysicalAnimationComponent.h"
Constructor: CreateDefaultSubobject<UPhysicalAnimationComponent>(TEXT("PhysicalAnimationComponent"))
Pointer Rules: UPhysicalAnimationComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UPhysicsHandleComponent
Include: "PhysicsEngine/PhysicsHandleComponent.h"
Constructor: CreateDefaultSubobject<UPhysicsHandleComponent>(TEXT("PhysicsHandleComponent"))
Pointer Rules: UPhysicsHandleComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UPhysicsThrusterComponent
Include: "PhysicsEngine/PhysicsThrusterComponent.h"
Constructor: CreateDefaultSubobject<UPhysicsThrusterComponent>(TEXT("PhysicsThrusterComponent"))
Pointer Rules: UPhysicsThrusterComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## URadialForceComponent
Include: "PhysicsEngine/RadialForceComponent.h"
Constructor: CreateDefaultSubobject<URadialForceComponent>(TEXT("RadialForceComponent"))
Pointer Rules: URadialForceComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.


## UPhysicsFieldComponent
Include: "PhysicsField/PhysicsFieldComponent.h"
Constructor: CreateDefaultSubobject<UPhysicsFieldComponent>(TEXT("PhysicsFieldComponent"))
Pointer Rules: UPhysicsFieldComponent*. Always use asterisk.
Instantiation: SetupAttachment(RootComponent) if it requires a physical transform.

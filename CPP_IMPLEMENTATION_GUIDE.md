# Unreal MCP Plugin - C++ Implementation Examples

## Overview

This document provides C++ code examples for implementing MCP tools and leveraging the plugin in your Unreal projects.

## Sample: Create a Custom MCP Tool

### Header File: MyCustomTool.h

```cpp
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/EngineSubsystem.h"
#include "MCPTool.h"
#include "MyCustomTool.generated.h"

/**
 * Example custom MCP tool for demonstrating plugin usage
 */
UCLASS()
class UNREALMCPDEMO_API UMyCustomTool : public UObject
{
    GENERATED_BODY()

public:
    /**
     * Initialize the tool with MCP plugin
     */
    UFUNCTION(BlueprintCallable, Category = "MCP")
    void Initialize();

    /**
     * Execute a sample tool command
     */
    UFUNCTION(BlueprintCallable, Category = "MCP")
    void ExecuteSampleTool(const FString& ToolName);

    /**
     * Get system information via MCP
     */
    UFUNCTION(BlueprintCallable, Category = "MCP")
    FString GetSystemInfo();

    /**
     * Callback when tool execution completes
     */
    DECLARE_DELEGATE_TwoParams(FOnToolExecuteComplete, bool /*bSuccess*/, const FString& /*Result*/);
    FOnToolExecuteComplete OnToolExecuteComplete;

private:
    // Reference to MCP plugin interface
    class IMCPPluginInterface* MCPInterface;

    /**
     * Handle tool execution result
     */
    void OnToolExecuted(bool bSuccess, const FString& Result);
};
```

### Implementation File: MyCustomTool.cpp

```cpp
#include "MyCustomTool.h"
#include "MCPPluginInterface.h"
#include "Modules/ModuleManager.h"

void UMyCustomTool::Initialize()
{
    // Get the MCP plugin module
    if (FModuleManager::Get().IsModuleLoaded(TEXT("UnrealMCP")))
    {
        IMCPPluginInterface* MCPModule = 
            FModuleManager::GetModulePtr<IMCPPluginInterface>(TEXT("UnrealMCP"));
        
        if (MCPModule)
        {
            MCPInterface = MCPModule;
            UE_LOG(LogTemp, Warning, TEXT("MCP Tool initialized successfully"));
        }
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("UnrealMCP module not loaded"));
    }
}

void UMyCustomTool::ExecuteSampleTool(const FString& ToolName)
{
    if (!MCPInterface)
    {
        UE_LOG(LogTemp, Error, TEXT("MCP Interface not initialized"));
        return;
    }

    // Prepare tool parameters
    FMCPToolParams Params;
    Params.ToolName = ToolName;
    Params.Parameters = FJsonObjectWrapper();

    // Execute the tool
    MCPInterface->ExecuteToolAsync(
        Params,
        FSimpleDelegate::CreateUObject(this, &UMyCustomTool::OnToolExecuted)
    );

    UE_LOG(LogTemp, Warning, TEXT("Tool execution started: %s"), *ToolName);
}

FString UMyCustomTool::GetSystemInfo()
{
    FString SystemInfo = TEXT("System Information:\n");
    
    SystemInfo += FString::Printf(TEXT("OS: %s\n"), *FPlatformMisc::GetOperatingSystemId());
    SystemInfo += FString::Printf(TEXT("CPU Info: %s\n"), *FPlatformMisc::GetCPUBrand());
    SystemInfo += FString::Printf(TEXT("CPU Count: %d\n"), FPlatformMisc::NumberOfCores());
    SystemInfo += FString::Printf(TEXT("RAM: %.2f GB\n"), 
                                  (float)FPlatformMemory::GetPhysicalGBRam());
    SystemInfo += FString::Printf(TEXT("Engine Version: %s\n"), *FEngineVersion::Current().ToString());

    return SystemInfo;
}

void UMyCustomTool::OnToolExecuted(bool bSuccess, const FString& Result)
{
    if (bSuccess)
    {
        UE_LOG(LogTemp, Warning, TEXT("Tool executed successfully\n%s"), *Result);
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("Tool execution failed: %s"), *Result);
    }

    // Broadcast result
    OnToolExecuteComplete.ExecuteIfBound(bSuccess, Result);
}
```

---

## Sample: Game Mode Using MCP Plugin

### Header File: MCPDemoGameMode.h

```cpp
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "MCPDemoGameMode.generated.h"

class UMCPStatusWidget;
class UMyCustomTool;

/**
 * Demo game mode that initializes MCP plugin at startup
 */
UCLASS()
class UNREALMCPDEMO_API AMCPDemoGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    AMCPDemoGameMode();

    virtual void BeginPlay() override;

    UFUNCTION(BlueprintCallable, Category = "MCP")
    UMyCustomTool* GetMCPTool() const { return MCPTool; }

    UFUNCTION(BlueprintCallable, Category = "MCP")
    bool IsMCPConnected() const;

    UFUNCTION(BlueprintCallable, Category = "MCP")
    FString GetMCPStatus() const;

private:
    // MCP Tool reference
    UPROPERTY()
    UMyCustomTool* MCPTool;

    /**
     * Initialize the MCP plugin and tools
     */
    void InitializeMCP();

    /**
     * Setup player HUD with status display
     */
    void SetupHUD();
};
```

### Implementation File: MCPDemoGameMode.cpp

```cpp
#include "MCPDemoGameMode.h"
#include "MyCustomTool.h"
#include "Pawns/Pawn.h"
#include "GameFramework/PlayerController.h"

AMCPDemoGameMode::AMCPDemoGameMode()
    : MCPTool(nullptr)
{
    // Use the default pawn class
    DefaultPawnClass = APawn::StaticClass();
}

void AMCPDemoGameMode::BeginPlay()
{
    Super::BeginPlay();

    UE_LOG(LogTemp, Warning, TEXT("MCP Demo Game Mode initialized"));

    // Initialize MCP
    InitializeMCP();

    // Setup HUD
    SetupHUD();
}

void AMCPDemoGameMode::InitializeMCP()
{
    // Create the MCP tool
    MCPTool = NewObject<UMyCustomTool>(this);
    
    if (MCPTool)
    {
        MCPTool->Initialize();
        
        // Bind completion delegate
        MCPTool->OnToolExecuteComplete.BindDynamic(
            this, 
            &AMCPDemoGameMode::OnMCPToolExecuted
        );

        UE_LOG(LogTemp, Warning, TEXT("MCP Tool created and initialized"));
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("Failed to create MCP Tool"));
    }
}

void AMCPDemoGameMode::SetupHUD()
{
    APlayerController* PC = GetWorld()->GetFirstPlayerController();
    if (PC)
    {
        // Show MCP status in game console
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(
                -1, 
                15.0f, 
                FColor::Green, 
                FString::Printf(TEXT("MCP Plugin Status: %s"), *GetMCPStatus())
            );
        }
    }
}

bool AMCPDemoGameMode::IsMCPConnected() const
{
    // Check if MCP tool is properly initialized
    return MCPTool != nullptr;
}

FString AMCPDemoGameMode::GetMCPStatus() const
{
    if (IsMCPConnected())
    {
        return TEXT("CONNECTED");
    }
    return TEXT("DISCONNECTED");
}
```

---

## Sample: Blueprint-Callable Functions

### Header File: MCPBlueprintLibrary.h

```cpp
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MCPBlueprintLibrary.generated.h"

/**
 * Blueprint function library for easy MCP access from Blueprints
 */
UCLASS()
class UNREALMCPDEMO_API UMCPBlueprintLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /**
     * Check if MCP plugin is available
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "MCP")
    static bool IsMCPAvailable();

    /**
     * Get MCP plugin version
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "MCP")
    static FString GetMCPVersion();

    /**
     * Get list of available MCP tools
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "MCP")
    static TArray<FString> GetAvailableMCPTools();

    /**
     * Execute an MCP tool synchronously
     */
    UFUNCTION(BlueprintCallable, Category = "MCP")
    static FString ExecuteMCPTool(const FString& ToolName, const FString& Parameters);

    /**
     * Get system information
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "MCP")
    static FString GetSystemInformation();

    /**
     * Get MCP connection status
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "MCP")
    static bool GetMCPConnectionStatus();
};
```

### Implementation File: MCPBlueprintLibrary.cpp

```cpp
#include "MCPBlueprintLibrary.h"
#include "MCPPluginModule.h"
#include "Modules/ModuleManager.h"

bool UMCPBlueprintLibrary::IsMCPAvailable()
{
    return FModuleManager::Get().IsModuleLoaded(TEXT("UnrealMCP"));
}

FString UMCPBlueprintLibrary::GetMCPVersion()
{
    if (!IsMCPAvailable())
    {
        return TEXT("Not Available");
    }

    IMCPPluginModule* MCPModule = 
        FModuleManager::GetModulePtr<IMCPPluginModule>(TEXT("UnrealMCP"));
    
    return MCPModule ? MCPModule->GetPluginVersion() : TEXT("Unknown");
}

TArray<FString> UMCPBlueprintLibrary::GetAvailableMCPTools()
{
    TArray<FString> Tools;

    if (!IsMCPAvailable())
    {
        return Tools;
    }

    IMCPPluginModule* MCPModule = 
        FModuleManager::GetModulePtr<IMCPPluginModule>(TEXT("UnrealMCP"));
    
    if (MCPModule)
    {
        Tools = MCPModule->GetAvailableTools();
    }

    return Tools;
}

FString UMCPBlueprintLibrary::ExecuteMCPTool(const FString& ToolName, const FString& Parameters)
{
    if (!IsMCPAvailable())
    {
        return TEXT("ERROR: MCP Plugin not available");
    }

    IMCPPluginModule* MCPModule = 
        FModuleManager::GetModulePtr<IMCPPluginModule>(TEXT("UnrealMCP"));
    
    if (MCPModule)
    {
        return MCPModule->ExecuteTool(ToolName, Parameters);
    }

    return TEXT("ERROR: Failed to execute tool");
}

FString UMCPBlueprintLibrary::GetSystemInformation()
{
    FString Info = TEXT("System Info:\n");
    
    Info += FString::Printf(TEXT("Platform: %s\n"), *FPlatformProperties::PlatformName());
    Info += FString::Printf(TEXT("Engine: %s\n"), *FEngineVersion::Current().ToString());
    Info += FString::Printf(TEXT("CPU Cores: %d\n"), FPlatformMisc::NumberOfCores());

    return Info;
}

bool UMCPBlueprintLibrary::GetMCPConnectionStatus()
{
    if (!IsMCPAvailable())
    {
        return false;
    }

    IMCPPluginModule* MCPModule = 
        FModuleManager::GetModulePtr<IMCPPluginModule>(TEXT("UnrealMCP"));
    
    return MCPModule ? MCPModule->IsConnected() : false;
}
```

---

## Sample: Async Tool Execution

### Header File: MCPAsyncTask.h

```cpp
#pragma once

#include "CoreMinimal.h"
#include "Async/AsyncWork.h"
#include "Containers/List.h"

/**
 * Async task for executing MCP tools without blocking the main thread
 */
class FMCPAsyncTask : public FNonAbandonableTask
{
public:
    FMCPAsyncTask(const FString& InToolName, const FString& InParameters);

    // FNonAbandonableTask interface
    void DoWork();
    
    FORCEINLINE TStatId GetStatId() const 
    { 
        RETURN_QUICK_DECLARE_CYCLE_STAT(FMCPAsyncTask, STATGROUP_ThreadPoolAsyncTasks); 
    }

    // Result accessors
    bool IsSuccess() const { return bSuccess; }
    const FString& GetResult() const { return Result; }

private:
    FString ToolName;
    FString Parameters;
    bool bSuccess;
    FString Result;
};

// Typedef for async task pointer
typedef FAsyncTask<FMCPAsyncTask> FMCPAsyncTaskPtr;
```

### Implementation File: MCPAsyncTask.cpp

```cpp
#include "MCPAsyncTask.h"
#include "MCPPluginModule.h"
#include "Modules/ModuleManager.h"

FMCPAsyncTask::FMCPAsyncTask(const FString& InToolName, const FString& InParameters)
    : ToolName(InToolName)
    , Parameters(InParameters)
    , bSuccess(false)
    , Result(TEXT(""))
{
}

void FMCPAsyncTask::DoWork()
{
    if (!FModuleManager::Get().IsModuleLoaded(TEXT("UnrealMCP")))
    {
        Result = TEXT("ERROR: MCP Plugin not loaded");
        bSuccess = false;
        return;
    }

    IMCPPluginModule* MCPModule = 
        FModuleManager::GetModulePtr<IMCPPluginModule>(TEXT("UnrealMCP"));
    
    if (MCPModule)
    {
        Result = MCPModule->ExecuteTool(ToolName, Parameters);
        bSuccess = !Result.StartsWith(TEXT("ERROR"));
    }
    else
    {
        Result = TEXT("ERROR: Failed to get MCP module");
        bSuccess = false;
    }
}
```

---

## Usage Example: Calling from Game Code

```cpp
// In your actor or component class
void AMyActor::ExecuteToolAsync()
{
    // Create async task
    FMCPAsyncTask* AsyncTask = new FMCPAsyncTask(TEXT("GetSystemInfo"), TEXT(""));
    FMCPAsyncTaskPtr TaskPtr(AsyncTask);

    // Execute async
    TaskPtr->StartBackgroundTask();

    // Check result after task completes
    if (TaskPtr->IsWorkDone())
    {
        FMCPAsyncTask& Task = TaskPtr->GetTask();
        if (Task.IsSuccess())
        {
            UE_LOG(LogTemp, Warning, TEXT("Tool result: %s"), *Task.GetResult());
        }
    }
}
```

---

## Best Practices

### 1. Always Check Plugin Availability

```cpp
if (!FModuleManager::Get().IsModuleLoaded(TEXT("UnrealMCP")))
{
    // Handle case where plugin is not loaded
    return;
}
```

### 2. Use Async Execution for Long-Running Tools

```cpp
// Don't block the game thread
FMCPAsyncTaskPtr AsyncTask = 
    MakeShareable(new FAsyncTask<FMCPAsyncTask>(ToolName, Params));
AsyncTask->StartBackgroundTask();
```

### 3. Implement Error Handling

```cpp
FString Result = ExecuteMCPTool(ToolName, Params);
if (Result.StartsWith(TEXT("ERROR")))
{
    UE_LOG(LogTemp, Error, TEXT("Tool failed: %s"), *Result);
    // Handle error appropriately
}
```

### 4. Cache Tool List at Startup

```cpp
void AMyGameMode::BeginPlay()
{
    // Cache available tools once at startup
    AvailableTools = GetAvailableMCPTools();
}
```

### 5. Validate Parameters Before Execution

```cpp
if (ToolName.IsEmpty() || Parameters.IsEmpty())
{
    UE_LOG(LogTemp, Warning, TEXT("Invalid tool parameters"));
    return;
}
```

---

**Last Updated**: February 2026  
**Compatibility**: Unreal Engine 5.3+  
**Status**: Complete Examples

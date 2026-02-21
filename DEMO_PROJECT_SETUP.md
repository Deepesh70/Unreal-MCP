# Unreal MCP Demo Project Setup

## Project Structure

The demo project follows this directory structure:

```
UnrealMCP-Demo/
├── Binaries/                      # Compiled binaries
├── Content/
│   ├── Maps/
│   │   └── DemoMap.umap          # Minimal demonstration map
│   ├── Widgets/
│   │   └── WBP_MCPStatus.uasset  # Status display widget blueprint
│   └── Blueprints/
│       └── BP_MCPTestActor.uasset # Test actor with MCP integration
├── Intercooled/                   # Intermediate build files
├── Plugins/
│   └── UnrealMCP/                # The MCP plugin folder
│       ├── Binaries/
│       ├── Content/
│       ├── Intermediate/
│       ├── Resources/
│       ├── Source/
│       └── UnrealMCP.uplugin     # Plugin descriptor
├── Source/                        # Demo project C++ source (optional)
├── UnrealMCPDemo.uproject        # Project file
└── README.md                      # ReadMe for demo project
```

## .uproject Configuration

The `UnrealMCP-Demo.uproject` file should contain:

```json
{
  "FileVersion": 3,
  "EngineAssociation": "5.3",
  "Category": "AI/MCP",
  "Description": "Demo project for Unreal MCP Plugin - Minimal setup to test plugin functionality",
  "IsEnterprise": false,
  "Modules": [
    {
      "Name": "UnrealMCPDemo",
      "Type": "Runtime",
      "LoadingPhase": "Default"
    }
  ],
  "Plugins": [
    {
      "Name": "UnrealMCP",
      "Enabled": true,
      "MarketplaceURL": "",
      "BetaVersion": false,
      "IsExperimental": false,
      "Installed": false
    }
  ]
}
```

## How to Create the Demo Project

### Option 1: Manual Setup (Recommended for Testing)

1. **Create a new Unreal Engine 5.3+ project**
   - Use "Blank" template
   - C++ or Blueprint (either works)

2. **Copy the plugin into Plugins folder**
   ```
   cp -r /path/to/UnrealMCP ./Plugins/UnrealMCP
   ```

3. **Open the project and regenerate Visual Studio files**
   - File → Generate Visual Studio project files (if using C++)
   - Restart the Editor

4. **Enable the plugin**
   - Edit → Plugins → Search "UnrealMCP" → Enable → Restart

5. **Create the demo assets** (see next section)

### Option 2: Template-Based Setup

Create a template .uproject file with plugin pre-configured:

```powershell
# PowerShell example for Windows
New-Item -ItemType Directory -Path "UnrealMCP-Demo/Plugins" -Force
Copy-Item -Path "path/to/UnrealMCP" -Destination "UnrealMCP-Demo/Plugins/UnrealMCP" -Recurse
```

## Creating Demo Assets

### 1. Create DemoMap

**In Unreal Editor:**

1. File → New Level → Empty Level
2. Save As → `/Game/Maps/DemoMap`
3. Add actors:
   - One Player Start actor (for camera)
   - One Text Render Actor (for status display)
   - The WBP_MCPStatus widget (1 instance)

### 2. Create Status Widget (WBP_MCPStatus)

**Blueprint Widget Setup:**

- **Container**: Vertical Box with padding
- **Header Text**: "Unreal MCP Plugin - Demo"
- **Status Panel**: 
  - Status Label: "Plugin Status: [Connected/Disconnected]"
  - Version Info: "Version: 1.0"
  - Timestamp: Shows initialization time
- **Test Button**: 
  - Label: "Run Sample Tool"
  - OnClicked Event: Calls MCP tool
- **Output Log**: Text Box displaying results

**Blueprint Logic (Pseudo-code):**

```cpp
Event Construct:
  - Call MCP Plugin Get Status function
  - Update Status Label color (Green if connected, Red if not)
  - Display Version number

Event OnTestButtonClicked:
  - Call MCP Plugin Execute Tool function
  - Pass "GetSystemInfo" as tool name
  - Display result in Output Log
```

### 3. Create Test Actor (BP_MCPTestActor)

**Blueprint Actor Setup:**

- Collider component for interaction
- Event on BeginPlay:
  - Initialize MCP connection
  - Log initialization status
- Custom function to execute MCP commands

## Plugin Integration Points

### C++ Integration (Optional)

If using C++, create a simple game mode to initialize the plugin:

```cpp
// DemoGameMode.h
#pragma once
#include "GameFramework/GameModeBase.h"
#include "MCPPluginInterface.h"
#include "DemoGameMode.generated.h"

UCLASS()
class UNREALMCPDEMO_API ADemoGameMode : public AGameModeBase
{
  GENERATED_BODY()

public:
  ADemoGameMode();
  
  virtual void BeginPlay() override;
  
private:
  UPROPERTY()
  class UMCPPluginInterface* MCPInterface;
};
```

## Verification Checklist

- [ ] Plugin appears in Edit → Plugins
- [ ] Plugin shows as "Enabled"
- [ ] Output Log shows initialization message
- [ ] DemoMap loads without errors
- [ ] Status Widget displays "Connected"
- [ ] Test Button executes successfully
- [ ] Command results appear in widget output

## Testing Scenarios

### Scenario 1: Fresh Installation
1. Remove plugin from Plugins folder
2. Load the demo project (should fail gracefully)
3. Install plugin, restart
4. Load demo project (should work)

### Scenario 2: Plugin Disabled
1. Edit → Plugins → Disable UnrealMCP
2. Load demo project
3. Widget should show "Disconnected" status
4. Re-enable plugin and test again

### Scenario 3: Command Execution
1. Load DemoMap
2. Click "Run Sample Tool"
3. Verify output appears in widget
4. Check Output Log for debug info

## Distribution

To distribute this demo project:

1. **Compress the project**: 
   ```
   tar -czf UnrealMCP-Demo.tar.gz UnrealMCP-Demo/
   ```

2. **Remove build artifacts** (optional, to reduce size):
   - Delete `/Binaries`, `/Intermediate`, `/Saved` folders
   - Keep `/Source`, `/Content`, `/Plugins`

3. **Create installation instructions** (see QUICKSTART.md)

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Failed to load plugin" | Plugin not in correct folder | Move to `Plugins/UnrealMCP/` |
| Widget not showing | Plugin not enabled during map load | Enable plugin before opening map |
| "Tool not found" error | MCP tool not registered | Check plugin initialization logs |
| Status shows "Disconnected" | Plugin failed to initialize | Check Output Log for errors |

---

**Note**: This demo project is minimal and focused on verification. For production use, expand with more tools, better error handling, and comprehensive logging.

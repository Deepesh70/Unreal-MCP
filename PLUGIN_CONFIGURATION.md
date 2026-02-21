# Unreal MCP Plugin Configuration Guide

## Overview

This guide explains how to configure the Unreal MCP Plugin for first-time users. It covers installation, enablement, and verification steps with troubleshooting guidance.

## Pre-Installation Requirements

Before installing the plugin, ensure you have:

- **Unreal Engine 5.3** or higher
- **Windows, macOS, or Linux** operating system
- **Administrator access** (required for some plugin operations)
- **At least 500MB** free disk space
- **C++ compiler** (if building from source)

## Installation Methods

### Method 1: Plugin Package Installation (Recommended)

1. **Download the plugin**
   - Visit the [Unreal MCP GitHub Releases](https://github.com/Deepesh70/Unreal-MCP/releases)
   - Download the latest `.zip` file

2. **Locate your project folder**
   ```
   C:\Users\YourName\Documents\Unreal Projects\YourProject
   ```

3. **Create Plugins directory** (if needed)
   ```powershell
   # Windows PowerShell
   New-Item -ItemType Directory -Path "Plugins" -Force
   ```

   ```bash
   # macOS/Linux Terminal
   mkdir -p Plugins
   ```

4. **Extract plugin to Plugins folder**
   ```
   YourProject/Plugins/UnrealMCP/
   ```

5. **Verify directory structure**
   ```
   Plugins/
   └── UnrealMCP/
       ├── Binaries/
       ├── Content/
       ├── Resources/
       ├── Source/
       └── UnrealMCP.uplugin
   ```

### Method 2: Clone from GitHub

```bash
# Open terminal in your project's Plugins folder
cd YourProject/Plugins

# Clone the repository
git clone https://github.com/Deepesh70/Unreal-MCP.git UnrealMCP

cd ..
```

### Method 3: Submodule Integration

```bash
# Add as git submodule
git submodule add https://github.com/Deepesh70/Unreal-MCP.git Plugins/UnrealMCP
```

## Plugin Activation

### Step 1: Open Your Project

1. Launch Unreal Engine
2. Click **Open Project**
3. Select your project file (`.uproject`)
4. Click **Open**

### Step 2: Enable the Plugin

**If this is the first time:**

1. You'll see a popup: *"Missing plugin 'UnrealMCP'..."*
2. Click **Yes** to rebuild the plugin
3. Wait for compilation to complete (2-5 minutes)
4. Click **Restart Now** when prompted

**If no popup appears:**

1. Go to **Edit** → **Plugins**
2. Search for **"MCP"** or **"UnrealMCP"**
3. Check the **Enabled** checkbox
4. Click **Restart Now**

### Step 3: Verify Installation

After restart:

1. **Check Output Log** (Window → Developer Tools → Output Log)
2. **Look for these messages:**
   ```
   [UnrealMCP] Initializing Unreal MCP Plugin...
   [UnrealMCP] Plugin version: 1.0
   [UnrealMCP] MCP server connection established
   [UnrealMCP] Plugin initialized successfully
   ```

3. **Check Console Variables**
   - Type in the console: `mcp.status`
   - Should output plugin status and version

## Configuration Files

### .uproject Configuration

Edit `YourProject.uproject` to ensure the plugin is configured:

```json
{
  "FileVersion": 3,
  "EngineAssociation": "5.3",
  "Category": "",
  "Description": "",
  "Modules": [...],
  "Plugins": [
    {
      "Name": "UnrealMCP",
      "Enabled": true
    }
  ]
}
```

### UnrealMCP.uplugin Configuration

Located in `Plugins/UnrealMCP/UnrealMCP.uplugin`:

```json
{
  "FileVersion": 3,
  "Version": 1,
  "VersionName": "1.0",
  "FriendlyName": "Unreal MCP Plugin",
  "Description": "Model Context Protocol integration for Unreal Engine",
  "Category": "Procedural Generation",
  "CreatedBy": "Deepesh70",
  "CreatedByURL": "https://github.com/Deepesh70",
  "DocsURL": "",
  "MarketplaceURL": "",
  "SupportURL": "https://github.com/Deepesh70/Unreal-MCP/issues",
  "EngineVersion": "5.3.0",
  "CanContainContent": true,
  "Installed": false,
  "Modules": [
    {
      "Name": "UnrealMCP",
      "Type": "Runtime",
      "LoadingPhase": "Default"
    }
  ]
}
```

## Engine Configuration

### DefaultEngine.ini

Add the following lines to `Config/DefaultEngine.ini` for advanced plugin settings:

```ini
[/Script/UnrealMCP.MCPPluginSettings]
bEnableMCPServer=true
MCPServerPort=9000
bVerboseLogging=true
MaxConnectionTimeout=30
```

### DefaultInput.ini

Add button mappings for MCP tools (optional):

```ini
[/Script/Engine.InputSettings]
+ActionMappings=(ActionName="MCP_ExecuteSampleTool",Key=F11)
+ActionMappings=(ActionName="MCP_ShowStatus",Key=F12)
```

## Advanced Configuration

### Remote MCP Server Connection

To connect to a remote MCP server instead of local:

1. Edit `Config/DefaultEngine.ini`
2. Add:
   ```ini
   [/Script/UnrealMCP.MCPPluginSettings]
   bUseRemoteServer=true
   RemoteServerAddress=192.168.1.100
   RemoteServerPort=9000
   ```

### Logging Configuration

Enable detailed logging:

```ini
[Core.Log]
LogUnrealMCP=Verbose
LogMCPServer=Verbose
LogMCPTools=Verbose
```

View logs in:
- **Windows**: `Saved/Logs/YourProject.log`
- **macOS/Linux**: `Saved/Logs/YourProject.log`

### Disable Specific Tools

If you need to disable certain MCP tools:

```ini
[/Script/UnrealMCP.MCPPluginSettings]
DisabledTools=GetSystemInfo
DisabledTools=QueryAssets
```

## Network Configuration

### Firewall Settings

Ensure firewall allows connections:

**Windows Firewall:**
1. Settings → Privacy & Security → Windows Defender Firewall
2. Allow an app through firewall
3. Add `UE4Editor.exe` or `YourGame.exe`

**macOS:**
```bash
# Allow Unreal Engine through firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/Epic\ Games/UE_5.3/Engine/Binaries/Mac/UE4Editor.app/Contents/MacOS/UE4Editor
```

**Linux:**
```bash
# For UFW (Ubuntu)
sudo ufw allow 9000
```

## Performance Tuning

### Thread Configuration

```ini
[/Script/UnrealMCP.MCPPluginSettings]
MaxWorkerThreads=4
ThreadStackSize=1048576
```

### Memory Management

```ini
[/Script/UnrealMCP.MCPPluginSettings]
MaxBufferSize=16777216
EnableMemoryPooling=true
MemoryPoolPreAllocation=8388608
```

### Cache Settings

```ini
[/Script/UnrealMCP.MCPPluginSettings]
EnableToolCache=true
CacheTimeout=300
MaxCacheEntries=1000
```

## Uninstallation

### Complete Removal

1. **Disable the plugin**
   - Edit → Plugins → Search "MCP" → Uncheck Enabled

2. **Close the Editor**
   - Wait for any pending saves

3. **Delete plugin folder**
   ```powershell
   Remove-Item -Path "Plugins/UnrealMCP" -Recurse -Force
   ```

4. **Clean intermediate files**
   ```powershell
   Remove-Item -Path "Intermediate" -Recurse -Force
   Remove-Item -Path "Binaries" -Recurse -Force
   ```

5. **Regenerate project files** (C++ projects)
   - Right-click `.uproject` file
   - Select "Generate Visual Studio project files"

## Verification Checklist

After installation, verify:

- [ ] Plugin appears in Edit → Plugins
- [ ] Plugin shows as "Enabled"
- [ ] No errors in Output Log startup
- [ ] `mcp.status` console command returns valid status
- [ ] Can open a Level without crashes
- [ ] Can access Tools → MCP menu (if implemented)

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Plugin not appearing | Plugin not in correct path | Move to `Plugins/UnrealMCP/` |
| "Plugin failed to load" | Missing dependencies | Recompile: Right-click `.uproject` → "Compile" |
| Engine crashes on startup | Plugin incompatibility | Check engine version in `.uplugin` matches |
| "MCP server connection failed" | Network issue | Check firewall, verify server running |
| Memory leak warnings | Cache not clearing | Set reasonable `CacheTimeout` value |
| Performance degradation | Too many worker threads | Reduce `MaxWorkerThreads` in config |

## Getting Support

- **Documentation**: [QUICKSTART.md](QUICKSTART.md)
- **Issues**: [GitHub Issues](https://github.com/Deepesh70/Unreal-MCP/issues)
- **Wiki**: Check project wiki for examples
- **Discord**: Join community Discord (if available)

---

**Last Updated**: February 2026  
**Compatible with**: Unreal Engine 5.3+  
**Status**: Stable Release

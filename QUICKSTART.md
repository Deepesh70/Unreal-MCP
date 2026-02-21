# Unreal MCP Plugin - Quick Start Guide

## Prerequisites
- Unreal Engine 5.3 or higher
- The Unreal MCP Plugin
- Basic knowledge of Unreal Editor

## Installation Steps

### Step 1: Install the Plugin
1. Download the latest Unreal MCP plugin from the releases page
2. Place the plugin in your project's `Plugins` folder:
   ```
   YourProject/Plugins/UnrealMCP/
   ```
3. If the folder doesn't exist, create it

### Step 2: Enable the Plugin
1. Open your Unreal project
2. Go to **Edit** → **Plugins**
3. Search for "Unreal MCP"
4. Check the **Enabled** checkbox
5. Restart the Editor when prompted

### Step 3: Verify Installation
1. When the Editor restarts, open the **Output Log** (Window → Developer Tools → Output Log)
2. Look for the message: `[UnrealMCP] Plugin initialized successfully`
3. You should see a new menu item: **Tools** → **MCP**

### Step 4: Test the Plugin
1. Go to **Tools** → **MCP** → **Run Sample Tool**
2. Check the Output Log for successful execution
3. You should see the plugin status and command results

### Step 5: Load the Demo Map
1. In the Content Browser, navigate to:
   ```
   /Game/Maps/DemoMap
   ```
2. Double-click **DemoMap** to load it
3. You'll see a Demo Widget showing:
   - Plugin Status: **Connected**
   - Available Tools: List of MCP tools
   - Test Tool Button to execute a sample command

## Demo Widget Features

The Demo Map includes a widget that displays:

- **Plugin Status**: Shows connection state (Green = Connected, Red = Disconnected)
- **Status Details**: Plugin version and initialization time
- **Sample Tool Button**: Runs a test command to verify functionality
- **Output Console**: Shows command results in real-time

## Common Commands

Once the plugin is enabled, try these:

```
Tools → MCP → Get System Information
Tools → MCP → Query Local Assets
Tools → MCP → List Available Tools
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Plugin doesn't appear in Plugins list | Restart the Editor after placing plugin files |
| "Plugin initialized" message not showing | Check plugin is enabled in Edit → Plugins |
| Demo Map not found | Ensure Content Browser shows "View Options" with "Show Engine Content" and "Show Plugin Content" enabled |
| Widget doesn't show status | Verify plugin is loaded before loading the map |

## Next Steps

1. Review the [DEMO_PROJECT_SETUP.md](DEMO_PROJECT_SETUP.md) for detailed architecture
2. Check [PLUGIN_CONFIGURATION.md](PLUGIN_CONFIGURATION.md) for advanced setup
3. Explore available MCP tools in the Tools menu

## Getting Help

- Check the main [README.md](README.md) for general project information
- Review the [FAQ.md](FAQ.md) for common questions (coming soon)
- Submit issues on the [GitHub repository](https://github.com/Deepesh70/Unreal-MCP/issues)

---

**Last Updated**: February 2026  
**Plugin Version**: 1.0+  
**Unreal Engine Version**: 5.3+

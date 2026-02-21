# Unreal MCP Plugin

A comprehensive Model Context Protocol (MCP) integration for Unreal Engine, enabling AI-powered tools and services directly within your Unreal projects.

## Quick Links

- **⚡ [Quick Start (5 minutes)](QUICKSTART.md)** - Get up and running immediately
- **📚 [Full Documentation](#documentation)** - Comprehensive guides and references
- **🎮 [Demo Project](DEMO_PROJECT_SETUP.md)** - Minimal pre-configured project
- **❓ [FAQ & Troubleshooting](FAQ.md)** - Common questions and solutions
- **💻 [C++ Implementation Guide](CPP_IMPLEMENTATION_GUIDE.md)** - Code examples and best practices

## Features

✅ **Easy Integration** - Simple plugin installation and configuration  
✅ **MCP Protocol Support** - Full Model Context Protocol compliance  
✅ **Blueprint & C++ Support** - Works with both Blueprint and C++ projects  
✅ **Demo Project Included** - Minimal map with status widget for verification  
✅ **Async Tool Execution** - Non-blocking tool execution without freezing the game  
✅ **Comprehensive Logging** - Debug-friendly logging and error reporting  
✅ **Multi-Platform** - Windows, macOS, and Linux support  
✅ **Performance Optimized** - Configurable thread pools and caching  

## Supported Platforms

| Platform | Status | Version |
|----------|--------|---------|
| Windows | ✅ Supported | 5.3+ |
| macOS | ✅ Supported | 5.3+ |
| Linux | ✅ Supported | 5.3+ |
| Mobile | ⏳ Coming Soon | TBD |

## Getting Started

### 1. Installation (2 minutes)

```powershell
# Clone the plugin to your project
git clone https://github.com/Deepesh70/Unreal-MCP.git YourProject/Plugins/UnrealMCP
```

### 2. Enable the Plugin (1 minute)

1. Open your Unreal Engine 5.3+ project
2. Go to **Edit** → **Plugins**
3. Search for **"UnrealMCP"**
4. Check the **Enabled** checkbox
5. Restart the Editor

### 3. Verify Installation (1 minute)

1. Open the **Output Log** (Window → Developer Tools → Output Log)
2. Look for: `[UnrealMCP] Plugin initialized successfully`
3. Execute console command: `mcp.status`
4. You should see plugin version and connection status

### 4. Load Demo Map (1 minute)

1. Open **Content Browser**
2. Navigate to `/Game/Maps/DemoMap` (if exists)
3. Click to load the map
4. Check the status widget displays "**Connected**"
5. Click "**Run Sample Tool**" to verify functionality

---

## Documentation

### 📖 Essential Reading

- **[QUICKSTART.md](QUICKSTART.md)** - 5-step setup guide with troubleshooting
- **[PLUGIN_CONFIGURATION.md](PLUGIN_CONFIGURATION.md)** - Detailed configuration options
- **[FAQ.md](FAQ.md)** - Common questions and solutions

### 🎮 Project Setup

- **[DEMO_PROJECT_SETUP.md](DEMO_PROJECT_SETUP.md)** - Demo project structure and creation
- **[BLUEPRINT_WIDGET_EXAMPLE.md](BLUEPRINT_WIDGET_EXAMPLE.md)** - Status widget blueprint guide

### 💻 Development

- **[CPP_IMPLEMENTATION_GUIDE.md](CPP_IMPLEMENTATION_GUIDE.md)** - C++ examples and API reference

---

## Quick Command Reference

### Console Commands

```
mcp.status                    # Show current plugin status
mcp.test.tool                 # Execute a sample test tool
mcp.list.tools                # List all available tools
mcp.version                   # Show plugin version
```

### Configuration

Edit `Config/DefaultEngine.ini`:

```ini
[/Script/UnrealMCP.MCPPluginSettings]
bEnableMCPServer=true
MCPServerPort=9000
bVerboseLogging=true
MaxWorkerThreads=4
```

---

## Demo Project Features

The included demo project demonstrates:

✅ **Plugin Verification** - Status widget shows connection state  
✅ **Tool Execution** - Run sample MCP tools with one click  
✅ **Error Handling** - Graceful error display and logging  
✅ **Output Display** - Real-time command output in widget  
✅ **Best Practices** - Example of proper plugin integration  

### Load the Demo Project

```powershell
# Clone and open
git clone https://github.com/Deepesh70/Unreal-MCP.git
cd Unreal-MCP
# Open UnrealMCPDemo.uproject in Unreal Engine 5.3+
```

---

## Usage Examples

### Blueprint

```
1. Create a Widget Blueprint
2. Add a Button actor
3. On Button Clicked event:
   → Call "MCP Execute Tool" function
   → Pass tool name and parameters
   → Display result in UI
```

**See**: [BLUEPRINT_WIDGET_EXAMPLE.md](BLUEPRINT_WIDGET_EXAMPLE.md)

### C++ Code

```cpp
// Get MCP Plugin Module
if (FModuleManager::Get().IsModuleLoaded(TEXT("UnrealMCP")))
{
    IMCPPluginInterface* MCP = 
        FModuleManager::GetModulePtr<IMCPPluginInterface>(TEXT("UnrealMCP"));
    
    // Execute a tool
    FString Result = MCP->ExecuteTool(TEXT("GetSystemInfo"), TEXT(""));
    UE_LOG(LogTemp, Warning, TEXT("Result: %s"), *Result);
}
```

**See**: [CPP_IMPLEMENTATION_GUIDE.md](CPP_IMPLEMENTATION_GUIDE.md)

---

## Troubleshooting

### Plugin Not Appearing?

1. Ensure plugin is in: `YourProject/Plugins/UnrealMCP/`
2. Right-click `.uproject` → "Generate Visual Studio project files"
3. Restart the Editor

### Connection Failed?

1. Check **Output Log** for error messages
2. Verify MCP server is running on configured port
3. Check firewall allows connections on port 9000
4. See [FAQ.md](FAQ.md) for detailed solutions

### Looking for More Help?

1. **[FAQ.md](FAQ.md)** - Comprehensive troubleshooting guide
2. **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step setup
3. **[GitHub Issues](https://github.com/Deepesh70/Unreal-MCP/issues)** - Report bugs or request features

---

## Project Structure

```
Unreal-MCP/
├── README.md                          # This file
├── QUICKSTART.md                      # 5-minute setup guide
├── PLUGIN_CONFIGURATION.md            # Configuration reference
├── DEMO_PROJECT_SETUP.md              # Demo project guide
├── BLUEPRINT_WIDGET_EXAMPLE.md        # Blueprint tutorial
├── CPP_IMPLEMENTATION_GUIDE.md        # C++ code examples
├── FAQ.md                             # Frequently asked questions
├── UnrealMCPDemo.uproject            # Demo project file
├── server.py                          # MCP server (reference)
└── [Plugin Source]
    ├── Binaries/
    ├── Source/
    ├── Content/
    └── UnrealMCP.uplugin
```

---

## Compatibility

| Requirement | Minimum | Recommended |
|------------|---------|------------|
| Engine | 5.3.0 | 5.4+ |
| OS | Windows 7, macOS 10.13, Ubuntu 18.04 | Latest |
| RAM | 8 GB | 16 GB |
| Disk Space | 1 GB | 2 GB |

---

## What's Included

### Documentation (7 Files)
- Quick Start Guide
- Full Configuration Reference
- Demo Project Setup Instructions
- Blueprint Widget Tutorial
- C++ Implementation Examples
- FAQ & Troubleshooting

### Demo Assets
- Minimal Unreal demo project
- Status widget blueprint example
- Sample game mode integration
- Test actor implementation

### Configuration
- Sample .uproject file
- Default engine configuration
- Network settings guide

---

## Contributing

We welcome contributions! To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

See individual issues on GitHub for specific areas needing help.

---

## License

This project is licensed under the [LICENSE](LICENSE) file in the repository.

---

## Support & Community

- **Issues & Bugs**: [GitHub Issues](https://github.com/Deepesh70/Unreal-MCP/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Deepesh70/Unreal-MCP/discussions)
- **Documentation**: See links at top of this README

---

## Version History

### v1.0 (Current)
- Initial stable release
- Core MCP protocol support
- Demo project with verification widget
- Comprehensive documentation
- Blueprint and C++ support

---

## Acknowledgments

- Built for Unreal Engine community
- Implements Model Context Protocol (MCP) standard
- Special thanks to all contributors and testers

---

**Last Updated**: February 21, 2026  
**Current Version**: 1.0  
**Status**: ✅ Stable Release

For the latest updates, visit: [GitHub Repository](https://github.com/Deepesh70/Unreal-MCP)

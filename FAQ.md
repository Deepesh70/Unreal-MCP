# Unreal MCP Plugin - FAQ & Troubleshooting

## General Questions

### What is the Unreal MCP Plugin?

The Unreal MCP (Model Context Protocol) Plugin is an integration for Unreal Engine that enables communication with AI-powered tools and services through the MCP standard. It allows developers to leverage AI capabilities directly within their Unreal projects.

### What versions of Unreal Engine are supported?

- **Minimum**: Unreal Engine 5.3
- **Recommended**: Unreal Engine 5.4 or higher
- **Tested on**: Windows, macOS, Linux

### Where can I find the plugin documentation?

- [QUICKSTART.md](QUICKSTART.md) - Get started in 5 minutes
- [PLUGIN_CONFIGURATION.md](PLUGIN_CONFIGURATION.md) - Detailed configuration guide
- [DEMO_PROJECT_SETUP.md](DEMO_PROJECT_SETUP.md) - Demo project instructions
- GitHub Issues & Discussions

### Is the plugin free?

Yes, the Unreal MCP Plugin is open-source and free to use under the project's license.

---

## Installation & Setup

### Q: I get "Plugin missing" error when opening my project. What should I do?

**A:** This means the editor can't find the plugin. Follow these steps:

1. **Check plugin location**: Ensure the plugin is in `YourProject/Plugins/UnrealMCP/`
2. **Right-click `.uproject` file** → "Generate Visual Studio project files"
3. **Recompile** the project (for C++ projects)
4. **Restart** the Editor

```powershell
# Windows - Regenerate files
Right-click YourProject.uproject → Generate Visual Studio project files
```

### Q: How do I install the plugin for the first time?

**A:** Follow these steps:

1. Download plugin from [GitHub Releases](https://github.com/Deepesh70/Unreal-MCP/releases)
2. Create `Plugins` folder in your project (if it doesn't exist)
3. Extract plugin to `Plugins/UnrealMCP/`
4. Restart the Engine (or open project)
5. Select "Yes" when prompted to rebuild the plugin
6. Wait for compilation (2-5 minutes)
7. Verify in Output Log

**See**: [PLUGIN_CONFIGURATION.md](PLUGIN_CONFIGURATION.md) for detailed steps

### Q: Can I use the plugin in source builds of Unreal Engine?

**A:** Yes! For source builds:

1. Clone plugin to `Engine/Plugins/Community/UnrealMCP/`
2. Regenerate project files
3. Recompile the engine
4. The plugin will be available to all projects

### Q: Do I need Visual Studio to use this plugin?

**A:** 
- **For Blueprints**: No, Visual Studio not required
- **For C++ projects**: Yes, Visual Studio (or clang on Linux/Mac) required
- **For editing plugin source**: Yes, recommended

---

## Plugin Activation & Verification

### Q: How do I enable the plugin after installation?

**A:** Two methods:

**Method 1: Via Editor Menu**
1. Go to **Edit** → **Plugins**
2. Search for **"MCP"** or **"UnrealMCP"**
3. Click the checkbox to enable
4. Restart the Editor

**Method 2: Via .uproject File**
```json
"Plugins": [
  {
    "Name": "UnrealMCP",
    "Enabled": true
  }
]
```

### Q: How do I verify the plugin is properly installed?

**A:** Check these indicators:

1. **Output Log** (Window → Developer Tools → Output Log)
   - Look for: `[UnrealMCP] Plugin initialized successfully`

2. **Plugins Menu**
   - Edit → Plugins → Search "MCP" → Should show "Enabled"

3. **Console Command**
   - Open console (grave key: `)
   - Type: `mcp.status`
   - Should output plugin version and connection status

4. **Tools Menu** (if implemented)
   - Should show new menu: **Tools** → **MCP**

### Q: Plugin appears enabled but shows as disconnected?

**A:** Try these steps:

1. **Check Output Log** for error messages
2. **Verify MCP server is running** (if using external server)
3. **Check firewall settings** (see [PLUGIN_CONFIGURATION.md](PLUGIN_CONFIGURATION.md))
4. **Increase logging verbosity**:
   - Add to `Config/DefaultEngine.ini`:
     ```ini
     [/Script/UnrealMCP.MCPPluginSettings]
     bVerboseLogging=true
     ```
5. **Restart the Editor** with logging enabled
6. **Check Saved/Logs/YourProject.log** for details

---

## Configuration Issues

### Q: Can I configure where the plugin looks for the MCP server?

**A:** Yes, edit `Config/DefaultEngine.ini`:

```ini
[/Script/UnrealMCP.MCPPluginSettings]
bUseRemoteServer=false
MCPServerPort=9000
MCPServerAddress=127.0.0.1
```

**Common configurations:**

```ini
# Local server (default)
bUseRemoteServer=false
MCPServerPort=9000

# Remote server
bUseRemoteServer=true
RemoteServerAddress=192.168.1.100
RemoteServerPort=9000
```

### Q: How do I enable debug logging?

**A:** Add to `Config/DefaultEngine.ini`:

```ini
[Core.Log]
LogUnrealMCP=Verbose
LogMCPServer=Verbose
LogMCPTools=Verbose

[/Script/UnrealMCP.MCPPluginSettings]
bVerboseLogging=true
```

Then check logs in:
- **Windows/Linux**: `Saved/Logs/YourProject.log`
- **macOS**: `~/Library/Logs/YourProject.log`

### Q: Can I disable specific MCP tools?

**A:** Yes, add to `Config/DefaultEngine.ini`:

```ini
[/Script/UnrealMCP.MCPPluginSettings]
DisabledTools=GetSystemInfo
DisabledTools=QueryAssets
DisabledTools=ListAllTools
```

---

## Demo Project & Testing

### Q: How do I load the demo project?

**A:** Follow these steps:

1. Download or clone the Unreal-MCP repository
2. Copy the demo project to a local folder
3. Open the `.uproject` file with Unreal Engine 5.3+
4. Say "Yes" to rebuild the plugin
5. Launch and verify the status widget shows "Connected"

**See**: [QUICKSTART.md](QUICKSTART.md) and [DEMO_PROJECT_SETUP.md](DEMO_PROJECT_SETUP.md)

### Q: The demo project won't open. What should I do?

**A:** Try these troubleshooting steps:

1. **Check Unreal Engine version**
   - Minimum required: 5.3
   - Open `.uproject` with correct version

2. **Rebuild the plugin**
   - Right-click `.uproject` → "Open with Rocket"
   - Choose Unreal Engine 5.3+
   - Confirm rebuild when prompted

3. **Check file integrity**
   - Verify all files were extracted correctly
   - Check for permission issues
   - Try re-downloading the project

4. **Check disk space**
   - Ensure 1GB+ free space for compilation
   - Check `Intermediate/` and `Binaries/` folders creating

5. **Review compilation errors**
   - Check the Compile Output window
   - Look for specific error messages
   - Search GitHub Issues for similar errors

### Q: How do I test if the plugin is working?

**A:** Methods to verify:

1. **Load the Demo Map**
   - Open DemoMap
   - Check status widget shows "Connected"
   - Click "Run Sample Tool"
   - Verify output appears

2. **Execute Console Command**
   - Open Console (grave key: `)
   - Type: `mcp.test.tool`
   - Should return result

3. **Check Output Log**
   - Window → Developer Tools → Output Log
   - Execute sample tool
   - Look for success/error messages

---

## Performance & Optimization

### Q: The plugin is slowing down my editor. What can I do?

**A:** Try these optimizations:

1. **Reduce worker threads** in `Config/DefaultEngine.ini`:
   ```ini
   [/Script/UnrealMCP.MCPPluginSettings]
   MaxWorkerThreads=2
   ```

2. **Disable caching** if not needed:
   ```ini
   EnableToolCache=false
   ```

3. **Reduce logging verbosity**:
   ```ini
   bVerboseLogging=false
   [Core.Log]
   LogUnrealMCP=Log
   ```

4. **Increase cache timeout**:
   ```ini
   CacheTimeout=600
   ```

### Q: Are there any memory leaks in the plugin?

**A:** The plugin is regularly tested, but report any suspected leaks:

1. **Enable memory tracking** in Editor Preferences
2. **Reproduce the issue** (steps that cause memory usage to grow)
3. **Screenshot memory stats** after X operations
4. **File a GitHub Issue** with reproduction steps and stats

---

## Network & Connectivity

### Q: The plugin can't connect to the MCP server. What's wrong?

**A:** Check these items:

1. **Is the MCP server running?**
   ```bash
   # Check if port 9000 is listening
   netstat -an | findstr :9000        # Windows
   lsof -i :9000                      # macOS/Linux
   ```

2. **Check firewall settings**
   - Windows Firewall: Allow `UE4Editor.exe` through firewall
   - macOS: System Preferences → Security & Privacy
   - Linux: `sudo ufw allow 9000`

3. **Verify server address/port**
   - Edit `Config/DefaultEngine.ini`
   - Confirm `MCPServerAddress` and `MCPServerPort` are correct

4. **Test connectivity manually**
   ```bash
   # Test connection (Windows)
   Test-NetConnection -ComputerName 127.0.0.1 -Port 9000
   
   # Test connection (Linux/macOS)
   nc -zv 127.0.0.1 9000
   ```

### Q: Can I use the plugin with a remote MCP server?

**A:** Yes! Configure the remote server:

```ini
[/Script/UnrealMCP.MCPPluginSettings]
bUseRemoteServer=true
RemoteServerAddress=your.server.com
RemoteServerPort=9000
```

**Security considerations:**
- Use HTTPS/SSL when available
- Implement authentication in your server
- Restrict network access via firewall rules

---

## Common Error Messages

### `[ERROR] Plugin initialization failed`

**Causes:**
- MCP server not running
- Port already in use
- Network connectivity issue

**Solutions:**
1. Verify MCP server is running
2. Check port number in config
3. Restart the Editor

---

### `[ERROR] Tool execution timeout`

**Causes:**
- Network latency
- MCP server overloaded
- Slow machine

**Solutions:**
1. Increase timeout in `Config/DefaultEngine.ini`:
   ```ini
   MaxConnectionTimeout=60
   ```
2. Reduce tool arguments/data size
3. Restart MCP server

---

### `[ERROR] Plugin not found in marketplace`

**Causes:**
- Plugin not yet released on marketplace
- Outdated plugin search index

**Solutions:**
- Install from GitHub releases instead
- Use source code directly
- Check GitHub Issues for status

---

## Uninstallation & Cleanup

### Q: How do I completely remove the plugin?

**A:** Follow these steps:

1. **Disable the plugin**
   - Edit → Plugins → Search "MCP" → Uncheck

2. **Close the Editor**

3. **Delete plugin folder**
   ```powershell
   Remove-Item -Path "Plugins/UnrealMCP" -Recurse -Force
   ```

4. **Clean intermediate files**
   ```powershell
   Remove-Item -Path "Intermediate" -Recurse -Force
   Remove-Item -Path "Saved\Logs" -Recurse -Force
   ```

5. **Regenerate project files** (C++ projects)
   - Right-click `.uproject` → "Generate Visual Studio project files"

6. **Recompile** (C++ projects)
   - Open Visual Studio solution
   - Build → Rebuild Solution

---

## Getting Help

### Where can I report bugs?

- **GitHub Issues**: [Deepesh70/Unreal-MCP/issues](https://github.com/Deepesh70/Unreal-MCP/issues)
- **Include in report**:
  - Engine version
  - Plugin version
  - OS and specs
  - Steps to reproduce
  - Screenshots/logs

### How do I request features?

- **GitHub Issues**: Use "Feature Request" template
- **Discussions**: Post in GitHub Discussions
- **Provide context**: Why you need it, use cases

### Where can I share feedback?

- **GitHub Discussions**: Community feedback
- **Surveys**: Participate in community surveys (if available)
- **Direct contact**: See project README for contact info

---

**Last Updated**: February 2026  
**Plugin Version**: 1.0+  
**Document Status**: Complete & Regularly Updated

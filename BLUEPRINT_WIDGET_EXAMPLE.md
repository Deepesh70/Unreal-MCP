# Unreal MCP Demo - Blueprint Widget Example

## WBP_MCPStatus Widget Blueprint

This is a Unreal Engine User Interface (UMG) Widget Blueprint that displays the plugin status and allows testing.

### Widget Layout Structure

```
Canvas Panel
├── Background Panel (Dark Gray)
│   └── Vertical Box
│       ├── Title Text (Large, White)
│       │   ├── Text: "Unreal MCP Plugin"
│       │   └── Font Size: 24
│       │
│       ├── Status Section (Horizontal Box)
│       │   ├── Status Indicator (Circle, Color-Coded)
│       │   ├── Status Text Box
│       │   │   ├── Label: "Status:"
│       │   │   └── Value: "Connected" (Green) or "Disconnected" (Red)
│       │   └── Version Info
│       │       └── Text: "Version: 1.0 | Init Time: [timestamp]"
│       │
│       ├── Divider (Horizontal Line)
│       │
│       ├── Available Tools Section
│       │   ├── Tools Label Text
│       │   └── Tools List Text Box (Read-Only)
│       │       ├── "Tool 1: Get System Information"
│       │       ├── "Tool 2: List Available Assets"
│       │       └── "Tool 3: Query Plugin Status"
│       │
│       ├── Test Section (Vertical Box)
│       │   ├── Instructions Text
│       │   │   └── "Click below to run a sample MCP tool:"
│       │   └── Sample Tool Button
│       │       ├── Label: "Run Sample Tool"
│       │       ├── Style: Accent Color Button
│       │       └── OnClicked: ExecuteSampleTool()
│       │
│       └── Output Console (Vertical Box)
│           ├── Console Header: "Output Console"
│           └── Output Text Box (Multi-line, Scrollable)
│               └── Default: "Ready. Click 'Run Sample Tool' to execute..."
```

### Size and Positioning

```
- Canvas Panel: Stack in Viewport (Full Screen)
- Background Panel: Padding (40, 40, 40, 40)
- Width: 600px
- Height: 700px
- Position: Center/Top aligned
- Horizontal Alignment: Center
- Vertical Alignment: Top
```

### Colors and Styling

```
Color Scheme:
- Background: #2D2D2D (Dark Gray)
- Text Primary: #FFFFFF (White)
- Text Secondary: #CCCCCC (Light Gray)
- Success/Connected: #00FF00 (Bright Green)
- Error/Disconnected: #FF0000 (Bright Red)
- Accent/Button: #0078D4 (Microsoft Blue)
- Border: #404040 (Medium Gray)
```

### Widget Blueprint Logic (Event Graph)

#### Event: Construct
```cpp
Execution Flow:
↓
Get MCP Plugin Reference
  ↓
  Call Get Plugin Status
    ↓
    Check if Connected?
      ├─ YES → Set Status Text to "Connected" (Green)
      │        Set Status Indicator Color to Green
      │        Get Plugin Version
      │        Display Version and Init Time
      │        Call Populate Available Tools
      │
      └─ NO  → Set Status Text to "Disconnected" (Red)
               Set Status Indicator Color to Red
               Disable Test Button
               Display Error Message
```

#### Function: Populate Available Tools
```cpp
Execution Flow:
↓
Get MCP Plugin Supported Tools List
  ↓
Loop Through Each Tool
  ├─ Append Tool Name to Tools Text Box
  ├─ Append Tool Description
  └─ Add Line Break
```

#### Event: On Sample Tool Button Clicked
```cpp
Execution Flow:
↓
Disable Button (Prevent Multiple Clicks)
  ↓
Append "[EXECUTING] Running sample tool..." to Output
  ↓
Call MCP Plugin Execute Tool
  ├─ Tool Name: "GetSystemInformation"
  ├─ Parameters: None or {} (empty)
  └─ OnComplete Callback: On Tool Execute Complete
      ↓
      Enable Button
        ↓
        Get Result from Callback
          ├─ Success?
          │   ├─ YES → Append "SUCCESS:" + Result to Output
          │   │        Change Output Text Color to Green
          │   │        Append Timestamp
          │   │
          │   └─ NO  → Append "ERROR:" + Error Message to Output
          │            Change Output Text Color to Red
          │
          ├─ Scroll Output to Bottom
          └─ Log to Unreal Output Log
```

### Event Bindings

| Event | Trigger | Action |
|-------|---------|--------|
| Construct | Widget Created | Initialize plugin connection |
| ButtonClicked | "Run Sample Tool" Button | Execute MCP sample command |
| OnToolComplete | MCP Execution Finished | Display result in output |

### Example Output Messages

**On Successful Load:**
```
[2026-02-21 10:30:15] Unreal MCP Plugin Status Check...
[2026-02-21 10:30:15] Status: Connected
[2026-02-21 10:30:15] Version: 1.0
[2026-02-21 10:30:15] Initialization Time: 245ms
[2026-02-21 10:30:15] Available Tools: 3
Ready. Click 'Run Sample Tool' to execute...
```

**On Tool Execution - Success:**
```
[2026-02-21 10:30:25] [EXECUTING] Running sample tool...
[2026-02-21 10:30:26] SUCCESS: GetSystemInformation
OS: Windows 10
RAM: 16GB
CPU: Intel Core i7
GPU: NVIDIA RTX 3080
Engine Version: 5.3.0
[2026-02-21 10:30:26] Tool execution completed in 523ms
```

**On Tool Execution - Error:**
```
[2026-02-21 10:30:27] [EXECUTING] Running sample tool...
[2026-02-21 10:30:28] ERROR: Tool execution failed
Reason: Plugin not fully initialized
Please restart the editor and try again
```

### Widget Variables (Blueprint Details Panel)

```
Variables to Create:

1. MCPPluginInterface (Reference to UMCPPluginInterface)
   - Variable Type: Object Reference
   - Default Value: None
   - Tooltip: "Reference to the MCP plugin interface"

2. bIsToolExecuting (Boolean)
   - Variable Type: Boolean
   - Default Value: False
   - Tooltip: "Flag to prevent multiple simultaneous executions"

3. StatusIndicatorColor (Linear Color)
   - Variable Type: Linear Color
   - Default Value: Red
   - Tooltip: "Color for the status indicator (Green/Red)"

4. ConnectionStatus (Text)
   - Variable Type: Text
   - Default Value: "Connecting..."
   - Tooltip: "Current connection status text"

5. OutputLogText (Text)
   - Variable Type: Text
   - Default Value: ""
   - Tooltip: "Accumulated output log"

6. AvailableToolsList (Array of Text)
   - Variable Type: Text Array
   - Tooltip: "List of available MCP tools"
```

### Widget Hierarchy (Detailed)

```
WBP_MCPStatus (UUserWidget)
├── Canvas Panel (SCanvas)
│   └── BackgroundPanel (UBorder)
│       ├── Color/Brush: Dark Gray #2D2D2D
│       └── VerticalBox (UVerticalBox)
│
├── VerticalBox
│   ├── [0] Title Section (UTextBlock)
│   │   ├── Text: "Unreal MCP Plugin - Status"
│   │   ├── Font Size: 24
│   │   ├── Color: White
│   │   └── Padding: 0, 0, 0, 20
│   │
│   ├── [1] Status Section (UHorizontalBox)
│   │   ├── [0] Status Indicator (UImage)
│   │   │   ├── Size: 20x20px
│   │   │   ├── Brush: Circle
│   │   │   ├── Color: Bound to StatusIndicatorColor
│   │   │   └── Padding: 0, 0, 10, 0
│   │   │
│   │   ├── [1] Status Info (UVerticalBox)
│   │   │   ├── [0] Status Text (UTextBlock)
│   │   │   │   ├── Text: Bound to ConnectionStatus
│   │   │   │   └── Color: White
│   │   │   │
│   │   │   └── [1] Version Text (UTextBlock)
│   │   │       ├── Text: Bound to VersionText
│   │   │       └── Color: Light Gray
│   │   │
│   │   └── Padding: 0, 0, 0, 15
│   │
│   ├── [2] Divider (UBorder)
│   │   ├── Brush: Line/Solid Color
│   │   ├── Color: #404040
│   │   ├── Height: 2
│   │   └── Padding: 0, 0, 0, 15
│   │
│   ├── [3] Tools Section (UVerticalBox)
│   │   ├── [0] Tools Label (UTextBlock)
│   │   │   ├── Text: "Available Tools"
│   │   │   ├── Font Size: 16
│   │   │   └── Padding: 0, 0, 0, 10
│   │   │
│   │   └── [1] Tools List (UTextBlock)
│   │       ├── Text: Bound to ToolsListText
│   │       ├── Is Read Only: True
│   │       ├── Wrap Text: True
│   │       └── Color: Light Gray
│   │
│   ├── [4] Test Section (UVerticalBox)
│   │   ├── [0] Instructions (UTextBlock)
│   │   │   ├── Text: "Click the button below to run a sample tool:"
│   │   │   ├── Color: Light Gray
│   │   │   └── Padding: 0, 20, 0, 10
│   │   │
│   │   └── [1] Test Button (UButton)
│   │       ├── Label: "Run Sample Tool"
│   │       ├── Style: Accent (Blue)
│   │       ├── Size: 200x40px
│   │       └── OnClicked → Run_Sample_Tool_Event
│   │
│   ├── [5] Output Section (UVerticalBox)
│   │   ├── [0] Output Label (UTextBlock)
│   │   │   ├── Text: "Output Console"
│   │   │   ├── Font Size: 14
│   │   │   └── Padding: 0, 20, 0, 10
│   │   │
│   │   └── [1] Output Log (UEditableTextBox)
│   │       ├── Text: Bound to OutputLogText
│   │       ├── Is Multi-line: True
│   │       ├── Read Only: True
│   │       ├── Color: White
│   │       ├── Background: Dark (#1a1a1a)
│   │       ├── Height: 150px
│   │       └── Scrollbar: Enabled
```

### How to Create in Unreal Editor

1. **Create New Widget Blueprint**
   - Content Browser → Create Asset → Widget Blueprint
   - Name it: `WBP_MCPStatus`
   - Click "Create Widget Blueprint"

2. **Design the Widget (Designer Tab)**
   - Drag Canvas Panel to root
   - Inside Canvas Panel, add Border (BackgroundPanel)
   - Inside Border, add Vertical Box
   - Add child widgets as per hierarchy above
   - Use Details panel to customize colors, fonts, sizes

3. **Implement Logic (Graph Tab)**
   - Right-click in Graph area → Add Event → Construct
   - Implement the Event: Construct logic (see above)
   - Create Function: Populate Available Tools
   - Create Function: Execute Sample Tool
   - Wire up button OnClicked event

4. **Test the Widget**
   - Compile and Save
   - Create a Level
   - Add Widget to viewport (Level Blueprint or Game Mode)
   - Play in Editor and verify

---

**Note**: This example is a template. Adapt color schemes, layout, and functionality based on your specific design requirements.

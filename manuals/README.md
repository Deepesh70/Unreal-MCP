# Unreal-MCP — Project Manual

> **What is this?** A complete documentation module for the Unreal-MCP AI Engine. Everything about how the project works, how it evolved, what mistakes were made, and how to use it — written so anyone can understand.

---

## 📂 Folder Structure

```
manuals/
├── README.md                      ← You are here
├── history/                       ← How we got here (mistakes, evolution, lessons)
│   ├── 01_origins.md              ← How the project started
│   ├── 02_mistakes_and_lessons.md ← What went wrong and what we learned
│   └── 03_architecture_evolution.md ← How the design changed over time
├── architecture/                  ← How everything works NOW
│   ├── 01_system_overview.md      ← The big picture
│   ├── 02_mcp_tools.md            ← Every tool documented
│   ├── 03_websocket_bridge.md     ← How Python talks to Unreal
│   └── 04_ide_integration.md      ← How Cursor/Copilot/Antigravity connect
├── guides/                        ← Step-by-step instructions
│   ├── 01_setup.md                ← How to install and run
│   ├── 02_connecting_your_ide.md  ← IDE configuration for every major IDE
│   └── 03_unreal_plugins.md       ← What Unreal plugins to enable
└── progress/                      ← Tracking our work
    ├── phases.md                  ← Phase completion status
    └── validation.md              ← Test results and metrics
```

## Quick Links

- **New here?** Start with [System Overview](architecture/01_system_overview.md)
- **Want to use it?** Go to [Setup Guide](guides/01_setup.md)
- **Want to understand the history?** Read [Origins](history/01_origins.md) → [Mistakes](history/02_mistakes_and_lessons.md) → [Evolution](history/03_architecture_evolution.md)
- **Checking progress?** See [Phases](progress/phases.md)

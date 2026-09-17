# 📚 Unreal-MCP Documentation

Welcome to the comprehensive documentation for **Unreal-MCP**, the high-performance Model Context Protocol (MCP) and multi-agent AI interface for Unreal Engine.

---

## 🗺️ Documentation Sitemap

### 🚀 [Getting Started](getting_started/)
Step-by-step instructions to get up and running quickly:
* **[01. Installation Guide](getting_started/01_installation.md)**: Python environment, dependencies, and CLI setup.
* **[02. Unreal Engine Configuration](getting_started/02_unreal_setup.md)**: Enabling the Remote Control Web Interface and Python execution in UE5.
* **[03. IDE & Client Integration](getting_started/03_ide_configuration.md)**: Configuring VS Code, Antigravity, Cursor, and Claude Desktop with MCP.

### 🏛️ [Architecture & Internals](architecture/)
In-depth technical specifications and protocol details:
* **[01. System Architecture Overview](architecture/01_system_overview.md)**: End-to-end design, layers, and message passing flow.
* **[02. WebSocket & Remote Control Bridge](architecture/02_websocket_bridge.md)**: Communication protocol between FastMCP and Unreal Engine's C++ core.
* **[03. SaaS Cloud Relay Architecture](architecture/03_saas_relay_architecture.md)**: NAT/firewall traversal strategy and standalone relay app architecture.
* **[04. Multi-Agent Generative Pipeline](architecture/04_multi_agent_pipeline.md)**: Spatial reasoning, scene hierarchy, and multimodal vision verification.

### 📖 [Guides & Workflows](guides/)
Practical tutorials for common workflows:
* **[01. Actor Spawning & Transforms](guides/01_actor_manipulation.md)**: Working with primitive shapes, lights, cameras, and coordinate spaces.
* **[02. Combat & Weapon Attachment](guides/02_combat_and_weapons.md)**: Attaching weapons to character sockets and setting up combat mechanics.
* **[03. Animation Retargeting](guides/03_animation_retargeting.md)**: Automating IK Rig and IK Retargeter pipelines across character skeletons.
* **[04. C++ Class Generation](guides/04_cpp_codegen.md)**: Compiling Blueprint JSON definitions directly into native Unreal C++ source.
* **[05. Web UI & WebSocket Integration](guides/05_web_ui_integration.md)**: Connecting Next.js frontends to the agent platform via FastAPI WebSockets.

### 📑 [Reference](reference/)
Exhaustive reference sheets:
* **[Tool Dictionary](reference/tool_dictionary.md)**: All FastMCP tools, argument types, and return values.
* **[Asset Dictionary](reference/asset_dictionary.md)**: Standard asset paths, materials, and engine types.

### 🔬 [Research & Papers](research/)
* **[Academic Research Paper](research/research_paper.md)**: Formal paper outlining the architecture and experimental benchmarks.
* **[LaTeX Paper Source](research/research_paper.tex)**: Compile-ready LaTeX manuscript.

### 🎓 [Interview & Masterclass](interview/)
* **[Technical Masterclass](interview/technical_masterclass.md)**: Detailed code-by-code mastery of FastMCP, transports, and Remote Control.
* **[System Design Defense](interview/system_design_defense.md)**: High-level architectural defense and technical interview Q&A.

# Changelog

All notable changes to the **Unreal-MCP** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] - 2026-09-17

### Added
- **Production Package Architecture**: Unified multi-agent system (`agents/`) and API servers under the primary `unreal_mcp` namespace.
- **Unified CLI**: Support for subcommands (`unreal-mcp serve`, `unreal-mcp agent`, `unreal-mcp api`, `unreal-mcp bridge`).
- **Diátaxis Documentation System**: Centralized docs into `docs/getting_started/`, `docs/architecture/`, `docs/guides/`, `docs/reference/`, `docs/research/`, and `docs/interview/`.
- **Organized Examples & Cookbooks**: Structured demo scenes (`examples/demos/`), workflow automation recipes (`examples/recipes/`), and blueprints (`examples/blueprints/`).
- **Dedicated Scripts Directory**: Moved build and configuration utilities into `scripts/`.
- **Packaging Standards**: Upgraded `pyproject.toml` with grouped optional dependencies (`agent`, `api`, `codegen`, `dev`, `all`).

### Changed
- Converted root scripts (`server.py`, `agent.py`, `api_server.py`, `ide_bridge.py`) into lightweight backward-compatible launcher shims.
- Cleaned root workspace by relocating scratch and demo files.

---

## [0.1.0] - 2026-03-14

### Added
- Initial Model Context Protocol (MCP) server for Unreal Engine 5.
- Remote Control Web Interface WebSocket bridge.
- Actor spawning, transformation, and property inspection tools.
- Character socket mounting and combat mechanics tools.
- IK Rig animation retargeting tools.
- Multi-model agent backends (Groq, Ollama, Gemini).
- C++ class generation engine from JSON Blueprint definitions.
- RAG blueprint vector store via ChromaDB and HuggingFace MiniLM embeddings.

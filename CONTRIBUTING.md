# Contributing to Unreal-MCP

Thank you for your interest in contributing to **Unreal-MCP**! This document provides guidelines and instructions for contributing to the repository.

---

## 🛠️ Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Deepesh70/Unreal-MCP.git
cd Unreal-MCP
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate
```

### 3. Install in Editable Mode with Dependencies
```bash
pip install -e ".[all]"
```

---

## 📁 Repository Organization

Please follow the established repository architecture:
* **`unreal_mcp/`**: Canonical Python package source code.
  * `core/`: Connection, logging, settings.
  * `server/`: FastMCP server runtime.
  * `api/`: FastAPI server and IDE bridge.
  * `agents/`: Multi-agent pipeline, builder, hierarchy, vision, and RAG vector store.
  * `tools/`: MCP tool implementations.
  * `codegen/`: C++ code generator and Jinja2 templates.
  * `cli/`: Unified command-line interface.
* **`docs/`**: Central documentation structured according to the Diátaxis framework (`getting_started/`, `architecture/`, `guides/`, `reference/`, `research/`, `interview/`).
* **`examples/`**: Demos, workflow recipes, and architectural blueprints.
* **`scripts/`**: Utility, build, and setup scripts.
* **`tests/`**: Automated unit and integration tests.

---

## 🧪 Testing Guidelines

Before submitting changes, ensure that all tests pass:

```bash
# Run unit & integration tests
pytest tests/

# Verify CLI commands
python -m unreal_mcp.cli --help
python -m unreal_mcp.cli agent
```

---

## 📝 Pull Request Workflow

1. Create a descriptive feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Commit your changes with clear semantic commit messages:
   ```bash
   git commit -m "feat(tools): add new lighting manipulation tool"
   ```
3. Push to your fork / remote and open a Pull Request using the repository's standard PR template.

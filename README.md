# ⚒️ ForgeArtisan AI
### Autonomous 3D Technical Artist & Game Engine MCP Copilot
*Built for the Meta Global AI Developer Hackathon (Indie Dev Track)*

[![Meta Model API](https://img.shields.io/badge/Meta%20Model%20API-Muse%20Spark%20•%20SAM%203.1-blue)](https://dev.meta.ai)
[![Protocol](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-green)](https://modelcontextprotocol.io)
[![Engine](https://img.shields.io/badge/Engine-Unity%20Editor%20•%20Unreal%20•%20Blender-orange)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20x64-lightgrey)]()

---

## 🎯 What is ForgeArtisan?

Current generative 3D AI tools produce single, un-editable **"blob meshes"** with melted geometry, noisy vertex counts, and no modularity—unusable in real game development.

**ForgeArtisan** functions like a real, skilled 3D Technical Artist. It connects directly into your active game engine (Unity Editor in prototype; Unreal Engine 5 & Blender in implementation) via an open **Model Context Protocol (MCP)** server:

1. **Autonomous Research:** Scours blueprints, technical specifications, and community modeling tricks on the web to determine exact proportions, bevel curves, and mechanical sub-components.
2. **Procedural Beveled Assembly:** Builds parametric compound models with **sub-millimeter bevels, chamfered corner loops, and curved aerodynamic wedges**—never raw un-beveled "programmer blocks".
3. **PBR Material & Weathering Calibration:** Sets physical material channels (Cast Iron, Polished Brass, Timber, Emissive Lanterns) with realistic roughness/metallic contrast.
4. **Closed-Loop Visual Critique (SAM 3.1):** Captures high-res scene camera renders from the engine, uses **SAM 3.1** to segment components and verify silhouette curvature against reference criteria, and executes self-correcting passes until high craft standards are satisfied!

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│     Full Stack Web Studio (FastAPI / Tailwind UI)      │
│     • Natural Language Chat & Control Panel            │
│     • Live Agentic Execution Stream (Turns 1-6)        │
│     • SAM 3.1 Visual Critique & Quality Score Gauge    │
└──────────────────────────┬─────────────────────────────┘
                           │ (HTTP REST / SSE)
┌──────────────────────────▼─────────────────────────────┐
│          ForgeArtisan Agentic Core & MCP Server        │
│                                                        │
│  [Meta AI Stack]                                       │
│  • Muse Spark: Procedural Geometry & Code Synthesizer  │
│  • SAM 3.1: Closed-Loop Visual Critic & Segmentation   │
│  • Researcher: Blueprint & Mechanical Specs Scraper    │
└──────────────────────────┬─────────────────────────────┘
                           │ (Localhost HTTP JSON RPC)
                           ▼
┌────────────────────────────────────────────────────────┐
│          Active Game Engine (Unity Editor)             │
│  `Assets/Editor/ForgeArtisanBridge.cs`                │
│  • Spawns & modifies procedural meshes in real time    │
│  • Builds compound objects with chamfered bevels       │
│  • Assigns PBR materials (Standard / URP Lit)          │
│  • Renders & returns scene camera snapshots to agent   │
└────────────────────────────────────────────────────────┘
```

---

## 📦 Windows Installation (.exe with PATH Option)

ForgeArtisan is distributed as a standalone Windows installer with an optional **"Add to PATH"** setting.

### Option A: Interactive Windows Installer (Batch / PowerShell)
1. Run `packaging\install.bat` (or right-click `Install-ForgeArtisan.ps1` ➔ *Run with PowerShell*).
2. The installer will prompt:
   ```text
   Add ForgeArtisan to user PATH environment variable? (Y/N) [Default: Y]
   ```
3. Type `Y` (or press Enter).
4. ForgeArtisan is now installed in `%LOCALAPPDATA%\ForgeArtisan`, added to your system PATH, and a desktop shortcut for **ForgeArtisan Studio** is created!

### Option B: Build Setup Wizard (.exe)
You can compile the Inno Setup script `packaging\ForgeArtisanSetup.iss` to produce `dist\ForgeArtisan-Setup.exe`.

---

## 🚀 Quick Start Guide

Once added to PATH, you can run `forge-artisan` from any terminal:

### 1. Check Engine Connection
```bash
forge-artisan status
```

### 2. Launch the Web Studio
```bash
forge-artisan ui
```
Open **http://127.0.0.1:7860** in your browser.

### 3. Run Autonomous Crafting via CLI
```bash
forge-artisan run "Create a vintage 4-4-0 American steam locomotive with curved cowcatcher, beveled cab, brass bell, and weathered cast-iron chassis"
```

### 4. Install Bridge into any Unity Project
```bash
forge-artisan install-unity-bridge "C:\MyGameProjects\MedievalQuest"
```

### 5. Launch as an MCP Server (for Muse Code / Claude / IDEs)
```bash
forge-artisan mcp
```

---

## 🔑 Environment & Meta Model API Key Setup

> **Note for Judges & Evaluators:** ForgeArtisan requires a Meta Model API key (or partner endpoint such as Fireworks/Modal/Baseten). Keys are kept strictly private and should never be committed to git.

1. Create your `.env` file from the provided template:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and set your credentials:
   ```env
   MODEL_API_KEY=your_actual_meta_api_key_here
   MODEL_API_BASE_URL=https://api.meta.ai/v1
   MODEL_NAME=muse-spark-1.3
   VISION_MODEL_NAME=muse-spark-1.3
   UNITY_BRIDGE_URL=http://127.0.0.1:8080
   ```
3. ForgeArtisan automatically discovers and loads `.env` from your working directory or `%LOCALAPPDATA%\ForgeArtisan\.env`.

---

## 🤖 Handoff to Muse Code CLI

ForgeArtisan's agent kit strictly follows the Meta Agent architecture pattern (as used in Meta's agent workshops):

To hand off this codebase to **Muse Code**:
```bash
cd forge-artisan/agent
muse
```

Provide the ground rules prompt:
```text
You are my coding assistant. I am extending the ForgeArtisan 3D Technical Artist Agent in this folder.
Ground rules:
* When I ask for something, build only that, then stop and report.
* Change only files in `artisan_agent/` and `agent_kit/tools/`.
* The model chooses every tool call: don't hard-code which tool runs when.
* Use Meta Model API (muse-spark-1.3 and sam-3.1).
Reply "Ready" and wait for my request.
```

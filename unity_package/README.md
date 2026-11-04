# ForgeArtisan: Unity Bridge Setup

`ForgeArtisanBridge.cs` is a drop-in C# Editor script that connects your active Unity Editor instance directly with the ForgeArtisan Autonomous 3D Technical Artist and MCP server.

---

## ⚡ 1-Minute Quick Start

### Method 1: Automatic Installation via CLI
Run from your terminal:
```bash
forge-artisan install-unity-bridge "C:\Path\To\Your\UnityProject"
```

### Method 2: Manual Drag & Drop
1. Open your Unity Project.
2. In the `Project` tab, navigate to `Assets/`.
3. Create an `Editor` folder if it doesn't already exist (`Assets/Editor`).
4. Copy `ForgeArtisanBridge.cs` into `Assets/Editor/`.

Unity will automatically compile the script and launch the local HTTP RPC listener on:
`http://127.0.0.1:8080/`

---

## 🧪 Verifying Connection

In Unity Editor's top menu bar, you will see a new menu item:
`ForgeArtisan` ➔ `Server Status`

Clicking it will display:
```
Server is active on http://127.0.0.1:8080/
Ready to receive agent commands.
```

In your terminal:
```bash
forge-artisan status
```
Output:
```
✅ Connected to Unity 2022.3.x (Scene: SampleScene) at http://127.0.0.1:8080
```

---

## 🛠️ Supported Procedural Capabilities
- **Beveled Boxes & Chamfered Edges:** Non-destructive rounded corners avoiding sharp CG edges.
- **Wedges & Curved Deflectors:** Aerodynamic sweeps (e.g. locomotive cowcatchers).
- **Compound Hierarchies:** Automatically sets parent transforms and local pivot offsets.
- **PBR Materials:** Standard & URP Lit shader parameters (BaseColor, Metallic, Smoothness, Emission).
- **Viewport Snapshot Camera:** High-res headless rendering for closed-loop SAM 3.1 visual critique.

"""ForgeArtisan Settings and Environment Configuration."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://api.meta.ai/v1"
DEFAULT_MODEL = "muse-spark-1.3"
DEFAULT_VISION_MODEL = "muse-spark-1.3"
DEFAULT_UNITY_URL = "http://127.0.0.1:8080"


def root_dir() -> Path:
    """The root directory of forge-artisan."""
    return Path(__file__).resolve().parent.parent.parent


def env_file_paths() -> list[Path]:
    """Candidate paths for .env file."""
    paths = [
        Path.cwd() / ".env",
        root_dir() / ".env",
        Path(os.path.expandvars(r"%LOCALAPPDATA%\ForgeArtisan\.env")),
        Path(__file__).resolve().parent.parent / ".env",
    ]
    return paths


def load_env_config():
    """Loads environment variables from available .env files."""
    for p in env_file_paths():
        if p.exists():
            load_dotenv(p, override=False)


# Auto-load on import
load_env_config()


def model() -> str:
    return os.environ.get("MODEL_NAME", DEFAULT_MODEL)


def vision_model() -> str:
    m = os.environ.get("VISION_MODEL_NAME", DEFAULT_VISION_MODEL)
    if m == "sam-3.1":
        # Meta's /v1/chat/completions endpoint serves multimodal vision through muse-spark-1.3
        return "muse-spark-1.3"
    return m


def unity_url() -> str:
    url = os.environ.get("UNITY_BRIDGE_URL", "")
    if url:
        return url
    port_file = workspace_dir() / "unity_bridge_port.txt"
    if port_file.exists():
        try:
            p = port_file.read_text(encoding="utf-8").strip()
            if p.isdigit():
                return f"http://127.0.0.1:{p}"
        except Exception:
            pass
    return DEFAULT_UNITY_URL


def workspace_dir(root: Path | None = None) -> Path:
    d = (root or root_dir()) / "workspace"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_api_key(key: str) -> Path:
    """Saves the API key to .env file in root and localappdata."""
    os.environ["MODEL_API_KEY"] = key
    target = root_dir() / ".env"
    
    # Also write to LocalAppData if installed
    local_env = Path(os.path.expandvars(r"%LOCALAPPDATA%\ForgeArtisan\.env"))
    
    content = f"MODEL_API_KEY={key}\nMODEL_API_BASE_URL=https://api.meta.ai/v1\n"
    target.write_text(content, encoding="utf-8")
    
    if local_env.parent.exists():
        try:
            local_env.write_text(content, encoding="utf-8")
        except Exception:
            pass
            
    return target

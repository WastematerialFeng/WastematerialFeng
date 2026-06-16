#!/usr/bin/env python3
"""Verify the documented or local Hermes provider configuration."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT / "config" / "hermes.yaml"


def _read_config(config_path: Path) -> str:
    if not config_path.exists():
        raise SystemExit(f"ERROR: missing config file: {config_path}")
    return config_path.read_text(encoding="utf-8")


def _read_env(env_path: Path | None) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path or not env_path.exists():
        return values
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _extract_scalar(config: str, key: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(key)}:\s*([^#\n]+)", config, re.MULTILINE)
    return match.group(1).strip() if match else None


def _resolve_env(key: str, file_env: dict[str, str]) -> str:
    return os.getenv(key) or file_env.get(key, "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Hermes Codex/GPT provider configuration")
    parser.add_argument("--target", help="Hermes home to verify, for example ~/.hermes")
    parser.add_argument("--config", help="Explicit hermes.yaml path to verify")
    parser.add_argument("--env-file", help="Explicit .env path to include in verification")
    args = parser.parse_args()

    if args.target:
        target = Path(args.target).expanduser().resolve()
        config_path = target / "config" / "hermes.yaml"
        env_path = target / ".env"
    else:
        config_path = Path(args.config).expanduser().resolve() if args.config else DEFAULT_CONFIG_PATH
        env_path = Path(args.env_file).expanduser().resolve() if args.env_file else None

    config = _read_config(config_path)
    file_env = _read_env(env_path)
    lowered = config.lower()

    mode = _resolve_env("HERMES_TOKEN_MODE", file_env) or _extract_scalar(config, "mode") or "unknown"
    default_provider = _extract_scalar(config, "default_provider") or "unknown"
    fallback_provider = _extract_scalar(config, "fallback_provider") or "unknown"

    codex_configured = "token_env: CODEX_TOKEN" in config
    gpt_configured = "token_env: GPT_TOKEN" in config
    duojie_in_config = "duojie" in lowered
    duojie_in_env = any("DUOJIE" in key.upper() for key in {**file_env, **os.environ})

    try:
        display_config = config_path.relative_to(ROOT)
    except ValueError:
        display_config = config_path

    print(f"config_file={display_config}")
    if env_path:
        print(f"env_file={env_path}")
    print(f"token_mode={mode}")
    print(f"default_provider={default_provider}")
    print(f"fallback_provider={fallback_provider}")
    print(f"codex_provider_configured={str(codex_configured).lower()}")
    print(f"gpt_provider_configured={str(gpt_configured).lower()}")
    print(f"codex_base_url_present={str(bool(_resolve_env('CODEX_BASE_URL', file_env))).lower()}")
    print(f"codex_token_present={str(bool(_resolve_env('CODEX_TOKEN', file_env))).lower()}")
    print(f"gpt_token_present={str(bool(_resolve_env('GPT_TOKEN', file_env))).lower()}")
    print(f"duojie_reference_in_config={str(duojie_in_config).lower()}")
    print(f"duojie_env_present={str(duojie_in_env).lower()}")

    if duojie_in_config or duojie_in_env:
        print("status=warning_duojie_reference_found")
        return 2

    if mode == "codex" or (mode == "auto" and default_provider == "codex" and fallback_provider == "codex"):
        print("status=codex_selected")
        return 0

    print("status=check_routing_rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

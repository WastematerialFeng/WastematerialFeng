#!/usr/bin/env python3
"""Apply this repository's Hermes defaults to a local Hermes config directory.

By default the script writes to ``~/.hermes``. Set ``HERMES_HOME`` or pass
``--target`` to point at an existing local Hermes installation/config directory.
Existing files are backed up unless ``--force`` is provided.
"""

from __future__ import annotations

import argparse
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CONFIG = ROOT / "config" / "hermes.yaml"
SOURCE_ENV = ROOT / ".env.example"


def _backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak.{stamp}")
    shutil.copy2(path, backup_path)
    print(f"backup={backup_path}")


def _render_local_env() -> str:
    values = {
        "FEISHU_APP_ID": os.getenv("FEISHU_APP_ID", ""),
        "FEISHU_APP_SECRET": os.getenv("FEISHU_APP_SECRET", ""),
        "FEISHU_VERIFICATION_TOKEN": os.getenv("FEISHU_VERIFICATION_TOKEN", ""),
        "FEISHU_ENCRYPT_KEY": os.getenv("FEISHU_ENCRYPT_KEY", ""),
        "CODEX_TOKEN": os.getenv("CODEX_TOKEN", ""),
        "CODEX_BASE_URL": os.getenv("CODEX_BASE_URL") or os.getenv("OPENAI_BASE_URL", ""),
        "GPT_TOKEN": os.getenv("GPT_TOKEN", ""),
        "HERMES_TOKEN_MODE": os.getenv("HERMES_TOKEN_MODE", "codex"),
    }
    return (
        "# Feishu app credentials\n"
        f"FEISHU_APP_ID={values['FEISHU_APP_ID']}\n"
        f"FEISHU_APP_SECRET={values['FEISHU_APP_SECRET']}\n"
        f"FEISHU_VERIFICATION_TOKEN={values['FEISHU_VERIFICATION_TOKEN']}\n"
        f"FEISHU_ENCRYPT_KEY={values['FEISHU_ENCRYPT_KEY']}\n"
        "\n"
        "# Hermes model/service tokens\n"
        "# HERMES_TOKEN_MODE=codex forces local Hermes to use Codex instead of Duojie.\n"
        f"CODEX_TOKEN={values['CODEX_TOKEN']}\n"
        f"CODEX_BASE_URL={values['CODEX_BASE_URL']}\n"
        f"GPT_TOKEN={values['GPT_TOKEN']}\n"
        "\n"
        "# Optional override: auto | codex | gpt\n"
        f"HERMES_TOKEN_MODE={values['HERMES_TOKEN_MODE']}\n"
    )


def _write_env_if_missing(target_env: Path, force: bool) -> None:
    if target_env.exists() and not force:
        print(f"env=kept_existing:{target_env}")
        return
    if target_env.exists():
        _backup(target_env)
    target_env.write_text(_render_local_env(), encoding="utf-8")
    print(f"env=written:{target_env}")


def apply(target: Path, force: bool) -> None:
    if not SOURCE_CONFIG.exists() or not SOURCE_ENV.exists():
        raise SystemExit("ERROR: source config or .env.example is missing")

    target = target.expanduser().resolve()
    config_dir = target / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    target_config = config_dir / "hermes.yaml"
    target_env = target / ".env"

    if target_config.exists() and not force:
        _backup(target_config)
    elif target_config.exists():
        _backup(target_config)

    shutil.copy2(SOURCE_CONFIG, target_config)
    _write_env_if_missing(target_env, force=force)

    print(f"hermes_home={target}")
    print(f"config=written:{target_config}")
    print("provider_default=codex")
    print("provider_fallback=codex")
    print("duojie_configured=false")
    print("next=fill tokens in .env, then start your local Hermes with this HERMES_HOME")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply local Hermes Feishu/Codex configuration")
    parser.add_argument(
        "--target",
        default=None,
        help="Hermes home/config root. Defaults to $HERMES_HOME or ~/.hermes.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the target .env from .env.example as well as config.",
    )
    args = parser.parse_args()

    target = Path(args.target or os.getenv("HERMES_HOME") or "~/.hermes")
    apply(target, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

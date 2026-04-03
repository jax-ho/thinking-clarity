from __future__ import annotations

import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "thinking-clarity"
SKILL_COPY_PATHS = [
    "SKILL.md",
    "agents",
    "references",
    "scripts",
    "workflows",
]


def install_skill_tree(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for relative in SKILL_COPY_PATHS:
        source = ROOT / relative
        target = destination / relative
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)


@contextmanager
def codex_home_environment(mode: str, install_skill: bool = False):
    if mode == "ambient":
        yield os.environ.copy()
        return

    real_home = Path.home()
    auth_source = real_home / ".codex" / "auth.json"

    with tempfile.TemporaryDirectory(prefix="thinking-clarity-home-") as tmpdir:
        home = Path(tmpdir)
        codex_home = home / ".codex"
        agents_home = home / ".agents"
        skills_home = codex_home / "skills"

        codex_home.mkdir(parents=True, exist_ok=True)
        skills_home.mkdir(parents=True, exist_ok=True)
        (agents_home / "skills").mkdir(parents=True, exist_ok=True)

        if auth_source.exists():
            shutil.copy2(auth_source, codex_home / "auth.json")

        if install_skill:
            install_skill_tree(skills_home / SKILL_NAME)

        env = os.environ.copy()
        env["HOME"] = str(home)
        env["CODEX_HOME"] = str(codex_home)
        yield env


@contextmanager
def claude_home_environment(mode: str, install_skill: bool = False):
    if mode == "ambient":
        yield os.environ.copy()
        return

    real_home = Path.home()
    settings_source = real_home / ".claude" / "settings.json"

    with tempfile.TemporaryDirectory(prefix="thinking-clarity-claude-home-") as tmpdir:
        home = Path(tmpdir)
        claude_home = home / ".claude"
        skills_home = claude_home / "skills"

        claude_home.mkdir(parents=True, exist_ok=True)
        skills_home.mkdir(parents=True, exist_ok=True)

        loaded_settings: dict = {}
        if settings_source.exists():
            shutil.copy2(settings_source, claude_home / "settings.json")
            try:
                loaded_settings = json.loads(settings_source.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                loaded_settings = {}

        if install_skill:
            install_skill_tree(skills_home / SKILL_NAME)

        env = os.environ.copy()
        env["HOME"] = str(home)
        for key, value in (loaded_settings.get("env") or {}).items():
            env[str(key)] = str(value)
        yield env

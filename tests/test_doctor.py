import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(PROJECT_ROOT / "src")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = SRC_DIR if not pythonpath else f"{SRC_DIR}{os.pathsep}{pythonpath}"
    return subprocess.run(
        [sys.executable, "-m", "haiku_scribe", *args],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_doctor_passes_after_setup(tmp_path):
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 0
    assert "Haiku Scribe doctor: ok" in result.stdout


def test_doctor_reports_missing_installation(tmp_path):
    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "missing agent file" in result.stdout
    assert "missing CLAUDE.md guidance block" in result.stdout
    assert "missing settings file" in result.stdout


def test_doctor_reports_unsafe_agent_drift(tmp_path):
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0
    agent = tmp_path / ".claude" / "agents" / "haiku-scribe.md"
    agent.write_text(agent.read_text(encoding="utf-8").replace("model: haiku", "model: sonnet"), encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "agent model is not haiku" in result.stdout


def test_doctor_reports_agent_web_access_drift(tmp_path):
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0
    agent = tmp_path / ".claude" / "agents" / "haiku-scribe.md"
    agent.write_text(agent.read_text(encoding="utf-8").replace("Browse web.", "Browse the web."), encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "agent does not forbid web access" in result.stdout


def test_doctor_reports_missing_deny_rule(tmp_path):
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0
    settings = tmp_path / ".claude" / "settings.json"
    settings.write_text('{"permissions":{"deny":[]}}', encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "missing deny rule: Read(**/*credential*)" in result.stdout


def test_doctor_reports_agent_content_drift(tmp_path):
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0
    agent = tmp_path / ".claude" / "agents" / "haiku-scribe.md"
    agent.write_text(agent.read_text(encoding="utf-8") + "\nextra trailing note\n", encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "agent file drifted from current contract (run setup to restore)" in result.stdout


def test_doctor_reports_hook_script_content_drift(tmp_path):
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0
    hook = tmp_path / ".claude" / "hooks" / "haiku-scribe-v1-2-nudge.py"
    hook.write_text(hook.read_text(encoding="utf-8") + "\nextra trailing note\n", encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "hook script drifted from current contract (run setup to restore)" in result.stdout


def test_doctor_reports_guidance_block_drift(tmp_path):
    assert run_cli("setup", "--home", str(tmp_path)).returncode == 0
    guidance = tmp_path / ".claude" / "CLAUDE.md"
    text = guidance.read_text(encoding="utf-8")
    # Simulate an external compressor mangling a line inside the managed block.
    text = text.replace(
        "Before loading raw repository context, classify remaining work.",
        "Before loading raw repository context, classify remaining work.\nBefore loading raw repository context, classify remaining work.",
    )
    guidance.write_text(text, encoding="utf-8")

    result = run_cli("doctor", "--home", str(tmp_path))

    assert result.returncode == 1
    assert "CLAUDE.md guidance block drifted from current contract (run setup to restore)" in result.stdout

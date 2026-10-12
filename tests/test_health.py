# Signature: Mourad.Soltani
"""Health / smoke tests for Milestone Invoice CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
EXAMPLE = ROOT / "examples" / "sample_plan.json"


def test_main_exists():
    assert MAIN.is_file()


def test_example_plan_exists():
    assert EXAMPLE.is_file()


def test_cli_help():
    result = subprocess.run(
        [sys.executable, str(MAIN), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "milestone" in result.stdout.lower() or "progress" in result.stdout.lower()


def test_cli_version():
    result = subprocess.run(
        [sys.executable, str(MAIN), "--version"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout
    assert "Mourad.Soltani" in result.stdout


def test_validate_only():
    result = subprocess.run(
        [sys.executable, str(MAIN), str(EXAMPLE), "--validate-only"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "valid" in result.stdout.lower()


def test_render_markdown():
    result = subprocess.run(
        [sys.executable, str(MAIN), str(EXAMPLE), "-f", "md"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    out = result.stdout
    assert "Invoice" in out
    assert "Milestone" in out or "milestone" in out.lower()
    assert "Mourad.Soltani" in out


def test_render_html():
    result = subprocess.run(
        [sys.executable, str(MAIN), str(EXAMPLE), "-f", "html"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "<html" in result.stdout.lower()
    assert "Mourad.Soltani" in result.stdout


def test_render_json():
    result = subprocess.run(
        [sys.executable, str(MAIN), str(EXAMPLE), "-f", "json"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "_computed" in data
    assert "total" in data["_computed"]


def test_invalid_plan_fails():
    bad = ROOT / "tests" / "_bad_plan.json"
    bad.write_text('{"client": "x"}', encoding="utf-8")
    try:
        result = subprocess.run(
            [sys.executable, str(MAIN), str(bad)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0
    finally:
        bad.unlink(missing_ok=True)

"""Exercise the documented default-marker Ruff normalization pipeline."""

from __future__ import annotations

import ast
import subprocess
import sys

import pytest

from scope_markers.api import format_source, strip_markers


def _ruff(source: str) -> str:
    """Format marker-free Python with Ruff's isolated defaults."""
    completed = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--isolated",
         "--stdin-filename", "example.py", "-"],
        input=source, text=True, capture_output=True, check=True,
    )
    return completed.stdout
####


def _normalize(source: str) -> str:
    """Compose default marker removal, ordinary formatting and marker insertion."""
    return format_source(_ruff(strip_markers(source)))
####


@pytest.mark.parametrize("source", [
    "def first(x):\n    if x:\n        return 1\n    return 0\n\ndef second():\n    return 2\n",
    "class Example:\n    def method(self):\n        try:\n            return [1,2]\n"
    "        except ValueError:\n            return []\n",
    'def example():\n    text = "####"\n    # Keep this ordinary comment.\n    return text\n',
])
def test_default_pipeline_is_stable_and_recovers_after_ruff(source: str) -> None:
    normalized = _normalize(source)
    assert _normalize(normalized) == normalized
    assert _normalize(_ruff(normalized)) == normalized
    assert ast.dump(ast.parse(normalized)) == ast.dump(ast.parse(source))
####


def test_ruff_after_markers_requires_full_normalization() -> None:
    source = "def first():\n    return 1\n\ndef second():\n    return 2\n"
    canonical = _normalize(source)
    rewritten = _ruff(canonical)
    assert rewritten != canonical
    assert format_source(rewritten) != canonical
    assert _normalize(rewritten) == canonical
####


def test_strip_pipeline_resets_legacy_marker_width_explicitly() -> None:
    source = "def example():\n    return 1\n###\n"
    assert "\n###\n" in format_source(source)
    assert "\n####\n" in _normalize(source)
####

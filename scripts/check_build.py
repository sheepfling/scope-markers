"""Build and smoke-test an installed wheel outside the source checkout."""

from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts._project import temporary_prefix

ROOT = Path(__file__).resolve().parents[1]
_SMOKE = """
from importlib.metadata import version
from scope_markers.api import __version__, format_source, strip_markers, format_markdown_source
assert __version__ == version("scope-markers")
source = "def example():\\n    return 1\\n"
formatted = format_source(source)
assert "####" in formatted
assert format_source(formatted) == formatted
assert strip_markers(formatted) == source
assert "####" in format_markdown_source("```python\\n" + source + "```\\n")
"""

def main() -> int:
    """Verify wheel packaging without reusing stale distribution artifacts."""
    with TemporaryDirectory(prefix=temporary_prefix("wheel")) as output:
        built = subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                # noinspection SpellCheckingInspection
                "--outdir",
                output,
            ],
            cwd=ROOT,
            check=False,
        ).returncode
        if built:
            return built
        ####
        environment = Path(output) / "consumer"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        wheel, = Path(output).glob("*.whl")
        installed = subprocess.run(
            [str(python), "-I", "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)],
            cwd=output, check=False,
        ).returncode
        if installed:
            return installed
        ####
        for arguments in (("-m", "scope_markers", "--help"),
                          ("-m", "scope_markers", "--version"),
                          ("-c", _SMOKE)):
            result = subprocess.run(
                [str(python), "-I", *arguments], cwd=output, check=False,
            ).returncode
            if result:
                return result
            ####
        ####
        return 0
    ####
####


if __name__ == "__main__":
    raise SystemExit(main())
####

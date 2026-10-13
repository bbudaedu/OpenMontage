"""A cache hit must report where it put the file, under either output key.

``_result_from_cache`` repointed ``data["output"]`` to the requested
destination but left ``data["output_path"]`` (used by ``video_compose`` and
``green_screen_processor``) naming the first call's file, so a hit returned
``artifacts=[b.mp4]`` alongside ``data["output_path"] == a.mp4``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.asset_cache import reset_default_asset_cache  # noqa: E402
from tools.base_tool import BaseTool, Determinism, ToolResult, ToolTier  # noqa: E402


class _OutputPathTool(BaseTool):
    name = "output_path_tool"
    version = "1.0.0"
    tier = ToolTier.CORE
    determinism = Determinism.DETERMINISTIC
    idempotency_key_fields = ["text"]

    def execute(self, inputs: dict) -> ToolResult:
        out = Path(inputs["output_path"])
        out.write_text(inputs["text"])
        return ToolResult(
            success=True, data={"output_path": str(out)}, artifacts=[str(out)]
        )


@pytest.fixture
def cache_on(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMONTAGE_ASSET_CACHE", "1")
    monkeypatch.setenv("OPENMONTAGE_ASSET_CACHE_DIR", str(tmp_path / "asset_cache"))
    reset_default_asset_cache()
    yield tmp_path
    reset_default_asset_cache()


def test_hit_repoints_output_path_to_the_requested_destination(cache_on: Path) -> None:
    tool = _OutputPathTool()
    tool.execute({"text": "x", "output_path": str(cache_on / "a.txt")})
    hit = tool.execute({"text": "x", "output_path": str(cache_on / "b.txt")})
    assert hit.from_cache is True
    assert hit.artifacts == [str(cache_on / "b.txt")]
    assert hit.data["output_path"] == str(cache_on / "b.txt")


def test_hit_does_not_invent_an_output_path_key(cache_on: Path) -> None:
    class _OutputTool(_OutputPathTool):
        name = "output_tool"

        def execute(self, inputs: dict) -> ToolResult:
            out = Path(inputs["output_path"])
            out.write_text(inputs["text"])
            return ToolResult(success=True, data={"output": str(out)}, artifacts=[str(out)])

    tool = _OutputTool()
    tool.execute({"text": "x", "output_path": str(cache_on / "a.txt")})
    hit = tool.execute({"text": "x", "output_path": str(cache_on / "b.txt")})
    assert hit.from_cache is True
    assert hit.data["output"] == str(cache_on / "b.txt")
    assert "output_path" not in hit.data

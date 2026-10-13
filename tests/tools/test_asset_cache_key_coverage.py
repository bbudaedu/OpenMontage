"""The asset cache key must cover every input that can change the output.

``cache_key()`` used to hash only ``idempotency_key_fields``. Those lists were
written before anything consumed them and most omit output-affecting inputs
(``subtitle_gen`` omits ``corrections``, ``color_grade`` omits ``custom_vf``,
``video_compose`` omits ``audio_path`` ...). With OPENMONTAGE_ASSET_CACHE on, a
call that differed only in such an input was served the earlier call's file.

The tests walk the registry instead of naming tools, so a field added to any
cacheable tool later is covered without editing this file.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.asset_cache import reset_default_asset_cache  # noqa: E402
from tools.base_tool import _is_cacheable  # noqa: E402
from tools.subtitle.subtitle_gen import SubtitleGen  # noqa: E402
from tools.tool_registry import registry  # noqa: E402

registry.ensure_discovered()

# Inputs that make every tool pass the cacheability gate (a pinned seed for
# SEEDED tools); the gate itself, not this file, decides who is cacheable.
_GATE_INPUTS = {"output_path": "/tmp/out.bin", "seed": 1}

# Written out here rather than imported: these steer how a call runs, not what
# it produces (schema_media/fal_media leave them out of their key fields).
_RUN_CONTROL = {"output_path", "resume_job", "job_path", "poll_timeout", "poll_interval"}


def _cacheable_fields() -> list[tuple[str, str]]:
    pairs = []
    for name in sorted(registry.list_all()):
        tool = registry.get(name)
        if not _is_cacheable(tool, dict(_GATE_INPUTS)):
            continue
        for field in sorted((tool.input_schema or {}).get("properties", {})):
            if field not in _RUN_CONTROL or field in tool.idempotency_key_fields:
                pairs.append((name, field))
    return pairs


_FIELDS = _cacheable_fields()


def test_there_are_cacheable_tool_fields_to_check() -> None:
    assert len(_FIELDS) > 50


@pytest.mark.parametrize(("tool_name", "field"), _FIELDS)
def test_every_input_field_changes_the_cache_key(tool_name: str, field: str) -> None:
    tool = registry.get(tool_name)
    base = dict(_GATE_INPUTS)
    a = tool.cache_key({**base, field: "probe-value-a"})
    b = tool.cache_key({**base, field: "probe-value-b"})
    assert a != b, f"{tool_name}.{field} does not reach the cache key"


def test_output_path_still_does_not_change_the_key() -> None:
    tool = SubtitleGen()
    seg = [{"start": 0.0, "end": 1.0, "text": "hi"}]
    assert tool.cache_key({"segments": seg, "output_path": "/a.srt"}) == tool.cache_key(
        {"segments": seg, "output_path": "/b.srt"}
    )


def test_a_declared_output_directory_stays_in_the_key() -> None:
    """threejs_asset_catalog installs into output_path, a directory that is
    part of its result: two directories must not share a cache entry."""
    tool = registry.get("threejs_asset_catalog")
    base = {"operation": "install", "catalog_id": "x"}
    assert tool.cache_key({**base, "output_path": "/a"}) != tool.cache_key(
        {**base, "output_path": "/b"}
    )


def test_run_control_inputs_do_not_split_the_key() -> None:
    """Polling and job bookkeeping must not turn a repeat into a miss."""
    tool = next(
        registry.get(n)
        for n in sorted(registry.list_all())
        if {"job_path", "poll_timeout"} <= set((registry.get(n).input_schema or {}).get("properties", {}))
        and _is_cacheable(registry.get(n), dict(_GATE_INPUTS))
    )
    base = {"prompt": "p", "output_path": "/a.bin"}
    assert tool.cache_key(base) == tool.cache_key(
        {**base, "output_path": "/b.bin", "job_path": "/j.json", "poll_timeout": 5, "poll_interval": 1}
    )


@pytest.fixture
def cache_on(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMONTAGE_ASSET_CACHE", "1")
    monkeypatch.setenv("OPENMONTAGE_ASSET_CACHE_DIR", str(tmp_path / "asset_cache"))
    reset_default_asset_cache()
    yield tmp_path
    reset_default_asset_cache()


def test_subtitle_corrections_are_not_served_a_stale_file(cache_on: Path) -> None:
    tool = SubtitleGen()
    seg = [{"start": 0.0, "end": 2.0, "text": "teh quick brown fox"}]
    first = tool.execute({"segments": seg, "format": "srt", "output_path": str(cache_on / "a.srt")})
    second = tool.execute(
        {
            "segments": seg,
            "format": "srt",
            "output_path": str(cache_on / "b.srt"),
            "corrections": {"teh": "the"},
        }
    )
    assert first.success and second.success
    assert second.from_cache is False
    assert "the quick brown fox" in (cache_on / "b.srt").read_text()

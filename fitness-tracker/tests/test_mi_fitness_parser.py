"""
Tests for the Mi Fitness ZIP parser.

Uses synthetic CSV data that mirrors the real Mi Fitness export format.
No credentials or phone access needed.
"""
import tempfile
import os
import pytest

from tests.fixtures.build_zips import build_mi_fitness_zip
from backend.parsers.mi_fitness import parse_mi_fitness_zip, preview_mi_fitness_zip


@pytest.fixture
def mi_fitness_zip(tmp_path):
    path = tmp_path / "mi_fitness_export.zip"
    path.write_bytes(build_mi_fitness_zip())
    return str(path)


# ── Steps ─────────────────────────────────────────────────────────────────────

class TestSteps:
    def test_correct_count(self, mi_fitness_zip):
        result = parse_mi_fitness_zip(mi_fitness_zip)
        assert len(result["steps"]) == 5

    def test_fields_present(self, mi_fitness_zip):
        steps = parse_mi_fitness_zip(mi_fitness_zip)["steps"]
        for r in steps:
            assert "date" in r
            assert "steps" in r
            assert r["source"] == "mi_fitness"

    def test_values_parsed(self, mi_fitness_zip):
        steps = parse_mi_fitness_zip(mi_fitness_zip)["steps"]
        first = next(r for r in steps if str(r["date"]) == "2025-10-01")
        assert first["steps"] == 8432
        assert first["calories"] == pytest.approx(312.0)
        assert first["active_minutes"] == 45


# ── Heart rate ────────────────────────────────────────────────────────────────

class TestHeartRate:
    def test_correct_count(self, mi_fitness_zip):
        result = parse_mi_fitness_zip(mi_fitness_zip)
        assert len(result["heartrate"]) == 6

    def test_bpm_is_integer(self, mi_fitness_zip):
        hr = parse_mi_fitness_zip(mi_fitness_zip)["heartrate"]
        for r in hr:
            assert isinstance(r["bpm"], int)
            assert 30 < r["bpm"] < 220

    def test_timestamp_is_datetime(self, mi_fitness_zip):
        from datetime import datetime
        hr = parse_mi_fitness_zip(mi_fitness_zip)["heartrate"]
        for r in hr:
            assert isinstance(r["timestamp"], datetime)


# ── Sleep ─────────────────────────────────────────────────────────────────────

class TestSleep:
    def test_correct_count(self, mi_fitness_zip):
        result = parse_mi_fitness_zip(mi_fitness_zip)
        assert len(result["sleep"]) == 5

    def test_sleep_stages_present(self, mi_fitness_zip):
        sleep = parse_mi_fitness_zip(mi_fitness_zip)["sleep"]
        for r in sleep:
            assert r.get("total_minutes") is not None
            assert r.get("deep_minutes") is not None

    def test_sleep_values(self, mi_fitness_zip):
        sleep = parse_mi_fitness_zip(mi_fitness_zip)["sleep"]
        first = next(r for r in sleep if str(r["date"]) == "2025-10-01")
        assert first["total_minutes"] == 452
        assert first["deep_minutes"] == 90
        assert first["rem_minutes"] == 110


# ── Activities ────────────────────────────────────────────────────────────────

class TestActivities:
    def test_correct_count(self, mi_fitness_zip):
        result = parse_mi_fitness_zip(mi_fitness_zip)
        assert len(result["activities"]) == 5

    def test_sport_types_mapped(self, mi_fitness_zip):
        activities = parse_mi_fitness_zip(mi_fitness_zip)["activities"]
        types = {a["activity_type"] for a in activities}
        # Numeric IDs 1, 5, 3 should map to run, walk, cycle
        assert "run" in types
        assert "walk" in types
        assert "cycle" in types

    def test_no_numeric_type_ids_remain(self, mi_fitness_zip):
        """Numeric Xiaomi sport type codes should all be mapped to strings."""
        activities = parse_mi_fitness_zip(mi_fitness_zip)["activities"]
        for a in activities:
            assert not a["activity_type"].isdigit(), (
                f"Sport type '{a['activity_type']}' was not mapped — "
                "add it to _SPORT_TYPE_MAP in mi_fitness.py"
            )

    def test_distance_in_meters(self, mi_fitness_zip):
        activities = parse_mi_fitness_zip(mi_fitness_zip)["activities"]
        run = next(a for a in activities if str(a["date"]) == "2025-10-01")
        assert run["distance_meters"] == pytest.approx(5230.0)

    def test_source_is_mi_fitness(self, mi_fitness_zip):
        activities = parse_mi_fitness_zip(mi_fitness_zip)["activities"]
        for a in activities:
            assert a["source"] == "mi_fitness"


# ── Preview ───────────────────────────────────────────────────────────────────

class TestPreview:
    def test_returns_counts(self, mi_fitness_zip):
        preview = preview_mi_fitness_zip(mi_fitness_zip)
        assert preview["counts"]["steps"] == 5
        assert preview["counts"]["heartrate"] == 6
        assert preview["counts"]["sleep"] == 5
        assert preview["counts"]["activities"] == 5

    def test_returns_date_ranges(self, mi_fitness_zip):
        preview = preview_mi_fitness_zip(mi_fitness_zip)
        assert "steps" in preview["date_ranges"]
        assert preview["date_ranges"]["steps"]["from"] == "2025-10-01"
        assert preview["date_ranges"]["steps"]["to"] == "2025-10-05"

    def test_returns_activity_type_breakdown(self, mi_fitness_zip):
        preview = preview_mi_fitness_zip(mi_fitness_zip)
        types = {item["type"] for item in preview["activity_types"]}
        assert "run" in types

    def test_no_errors(self, mi_fitness_zip):
        preview = preview_mi_fitness_zip(mi_fitness_zip)
        assert preview["errors"] == [], f"Parser errors: {preview['errors']}"

    def test_files_found(self, mi_fitness_zip):
        preview = preview_mi_fitness_zip(mi_fitness_zip)
        names = [f.upper() for f in preview["files_found"]]
        assert any("STEP" in n for n in names)
        assert any("HEART" in n for n in names)
        assert any("SLEEP" in n for n in names)
        assert any("ACTIVITY" in n for n in names)

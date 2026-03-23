"""
Tests for the Runkeeper ZIP parser.

Uses synthetic data matching the real Runkeeper export format (cardioActivities.csv + GPX files).
No credentials or phone access needed.
"""
import pytest
from datetime import date

from tests.fixtures.build_zips import build_runkeeper_zip
from backend.parsers.runkeeper import parse_runkeeper_zip, _parse_duration, _normalise_type


@pytest.fixture
def runkeeper_zip(tmp_path):
    path = tmp_path / "runkeeper_export.zip"
    path.write_bytes(build_runkeeper_zip())
    return str(path)


# ── Duration helper ───────────────────────────────────────────────────────────

class TestParseDuration:
    def test_hms_format(self):
        assert _parse_duration("1:23:45") == 5025

    def test_ms_format(self):
        assert _parse_duration("28:11") == 1691

    def test_zero(self):
        assert _parse_duration("0:00:00") == 0

    def test_invalid_returns_none(self):
        assert _parse_duration("not-a-time") is None


# ── Type normalisation ────────────────────────────────────────────────────────

class TestNormaliseType:
    def test_known_types(self):
        assert _normalise_type("Running") == "run"
        assert _normalise_type("Walking") == "walk"
        assert _normalise_type("Cycling") == "cycle"
        assert _normalise_type("Hiking") == "hike"

    def test_case_insensitive(self):
        assert _normalise_type("RUNNING") == "run"
        assert _normalise_type("running") == "run"

    def test_unknown_type_passthrough(self):
        # Unknown types should pass through lowercased, not raise
        result = _normalise_type("Paddle Boarding")
        assert result == "paddle boarding"


# ── Full ZIP parse ────────────────────────────────────────────────────────────

class TestRunkeeper:
    def test_correct_count(self, runkeeper_zip):
        result = parse_runkeeper_zip(runkeeper_zip)
        assert len(result["activities"]) == 4

    def test_source_is_runkeeper(self, runkeeper_zip):
        activities = parse_runkeeper_zip(runkeeper_zip)["activities"]
        for a in activities:
            assert a["source"] == "runkeeper"

    def test_types_mapped(self, runkeeper_zip):
        activities = parse_runkeeper_zip(runkeeper_zip)["activities"]
        types = {a["activity_type"] for a in activities}
        assert "run" in types
        assert "walk" in types
        assert "cycle" in types

    def test_distance_converted_to_meters(self, runkeeper_zip):
        activities = parse_runkeeper_zip(runkeeper_zip)["activities"]
        # First activity: 5.23 km → 5230 m
        run = next(a for a in activities if a["date"] == date(2025, 10, 2))
        assert run["distance_meters"] == pytest.approx(5230.0)

    def test_duration_parsed_from_hms(self, runkeeper_zip):
        activities = parse_runkeeper_zip(runkeeper_zip)["activities"]
        run = next(a for a in activities if a["date"] == date(2025, 10, 2))
        assert run["duration_seconds"] == 1691  # 28:11

    def test_heart_rate_parsed(self, runkeeper_zip):
        activities = parse_runkeeper_zip(runkeeper_zip)["activities"]
        run = next(a for a in activities if a["date"] == date(2025, 10, 2))
        assert run["avg_heart_rate"] == 156

    def test_calories_parsed(self, runkeeper_zip):
        activities = parse_runkeeper_zip(runkeeper_zip)["activities"]
        run = next(a for a in activities if a["date"] == date(2025, 10, 2))
        assert run["calories"] == pytest.approx(387.0)

    def test_date_is_date_object(self, runkeeper_zip):
        from datetime import date as date_type
        activities = parse_runkeeper_zip(runkeeper_zip)["activities"]
        for a in activities:
            assert isinstance(a["date"], date_type)


# ── GPX enrichment ────────────────────────────────────────────────────────────

class TestGPXEnrichment:
    def test_gpx_points_attached_when_file_present(self, runkeeper_zip):
        activities = parse_runkeeper_zip(runkeeper_zip)["activities"]
        gpx_run = next(a for a in activities if a["date"] == date(2025, 10, 6))
        assert gpx_run["gpx_points"] is not None
        assert len(gpx_run["gpx_points"]) == 3

    def test_gpx_points_none_when_no_file(self, runkeeper_zip):
        activities = parse_runkeeper_zip(runkeeper_zip)["activities"]
        # Oct 2 run has no GPX file listed
        no_gpx_run = next(a for a in activities if a["date"] == date(2025, 10, 2))
        assert no_gpx_run["gpx_points"] is None

    def test_gpx_point_structure(self, runkeeper_zip):
        activities = parse_runkeeper_zip(runkeeper_zip)["activities"]
        gpx_run = next(a for a in activities if a["date"] == date(2025, 10, 6))
        point = gpx_run["gpx_points"][0]
        assert "lat" in point
        assert "lon" in point
        assert "time" in point

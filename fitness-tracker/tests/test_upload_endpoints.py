"""
Tests for the FastAPI upload endpoints.

Sends synthetic ZIPs to the actual API routes and verifies the response shape
and database counts. Uses an in-memory SQLite DB so nothing touches fitness.db.
"""
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base, get_db
from backend.models import activity, health  # registers models with Base.metadata
from tests.fixtures.build_zips import build_mi_fitness_zip, build_runkeeper_zip


# ── Test DB setup ─────────────────────────────────────────────────────────────

@pytest.fixture
def test_client():
    """
    Create a TestClient backed by an isolated in-memory SQLite database.
    Each test gets a fresh DB — nothing persists between tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _zip_file(data: bytes, filename: str):
    return ("file", (filename, io.BytesIO(data), "application/zip"))


# ── Mi Fitness endpoint ───────────────────────────────────────────────────────

class TestMiFitnessUpload:
    def test_returns_200(self, test_client):
        res = test_client.post(
            "/api/upload/mi-fitness",
            files=[_zip_file(build_mi_fitness_zip(), "mi_fitness.zip")],
        )
        assert res.status_code == 200

    def test_response_shape(self, test_client):
        res = test_client.post(
            "/api/upload/mi-fitness",
            files=[_zip_file(build_mi_fitness_zip(), "mi_fitness.zip")],
        )
        data = res.json()
        assert "imported" in data
        assert "skipped" in data
        assert set(data["imported"].keys()) == {"activities", "steps", "heartrate", "sleep"}

    def test_correct_counts_imported(self, test_client):
        res = test_client.post(
            "/api/upload/mi-fitness",
            files=[_zip_file(build_mi_fitness_zip(), "mi_fitness.zip")],
        )
        imp = res.json()["imported"]
        assert imp["steps"] == 5
        assert imp["heartrate"] == 6
        assert imp["sleep"] == 5
        assert imp["activities"] == 5

    def test_duplicate_import_skips_all(self, test_client):
        zip_data = build_mi_fitness_zip()
        # First import
        test_client.post(
            "/api/upload/mi-fitness",
            files=[_zip_file(zip_data, "mi_fitness.zip")],
        )
        # Second import of same file
        res = test_client.post(
            "/api/upload/mi-fitness",
            files=[_zip_file(zip_data, "mi_fitness.zip")],
        )
        imp = res.json()["imported"]
        skip = res.json()["skipped"]
        assert imp["steps"] == 0
        assert imp["activities"] == 0
        assert skip["steps"] == 5
        assert skip["activities"] == 5

    def test_rejects_non_zip(self, test_client):
        res = test_client.post(
            "/api/upload/mi-fitness",
            files=[("file", ("data.csv", io.BytesIO(b"col1,col2\n1,2"), "text/csv"))],
        )
        assert res.status_code == 400

    def test_activities_queryable_after_import(self, test_client):
        test_client.post(
            "/api/upload/mi-fitness",
            files=[_zip_file(build_mi_fitness_zip(), "mi_fitness.zip")],
        )
        res = test_client.get("/api/activities")
        assert res.status_code == 200
        assert res.json()["total"] == 5


# ── Mi Fitness preview endpoint ───────────────────────────────────────────────

class TestMiFitnessPreview:
    def test_returns_200(self, test_client):
        res = test_client.post(
            "/api/upload/mi-fitness/preview",
            files=[_zip_file(build_mi_fitness_zip(), "mi_fitness.zip")],
        )
        assert res.status_code == 200

    def test_preview_does_not_persist_data(self, test_client):
        test_client.post(
            "/api/upload/mi-fitness/preview",
            files=[_zip_file(build_mi_fitness_zip(), "mi_fitness.zip")],
        )
        # Nothing should be in the DB after a preview
        res = test_client.get("/api/activities")
        assert res.json()["total"] == 0

    def test_preview_counts_match_import_counts(self, test_client):
        zip_data = build_mi_fitness_zip()

        preview = test_client.post(
            "/api/upload/mi-fitness/preview",
            files=[_zip_file(zip_data, "mi_fitness.zip")],
        ).json()

        imp = test_client.post(
            "/api/upload/mi-fitness",
            files=[_zip_file(zip_data, "mi_fitness.zip")],
        ).json()["imported"]

        assert preview["counts"]["activities"] == imp["activities"]
        assert preview["counts"]["steps"] == imp["steps"]
        assert preview["counts"]["heartrate"] == imp["heartrate"]
        assert preview["counts"]["sleep"] == imp["sleep"]


# ── Runkeeper endpoint ────────────────────────────────────────────────────────

class TestRunkeeperUpload:
    def test_returns_200(self, test_client):
        res = test_client.post(
            "/api/upload/runkeeper",
            files=[_zip_file(build_runkeeper_zip(), "runkeeper.zip")],
        )
        assert res.status_code == 200

    def test_correct_activity_count(self, test_client):
        res = test_client.post(
            "/api/upload/runkeeper",
            files=[_zip_file(build_runkeeper_zip(), "runkeeper.zip")],
        )
        assert res.json()["imported"]["activities"] == 4

    def test_duplicate_import_skips_all(self, test_client):
        zip_data = build_runkeeper_zip()
        test_client.post(
            "/api/upload/runkeeper",
            files=[_zip_file(zip_data, "runkeeper.zip")],
        )
        res = test_client.post(
            "/api/upload/runkeeper",
            files=[_zip_file(zip_data, "runkeeper.zip")],
        )
        assert res.json()["imported"]["activities"] == 0
        assert res.json()["skipped"]["activities"] == 4

    def test_activities_appear_in_list(self, test_client):
        test_client.post(
            "/api/upload/runkeeper",
            files=[_zip_file(build_runkeeper_zip(), "runkeeper.zip")],
        )
        res = test_client.get("/api/activities?source=runkeeper")
        assert res.json()["total"] == 4

"""
Integration tests for RecoverBuddy REST API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.seed_data import seed_database

@pytest.fixture(scope="module")
def client():
    seed_database()
    with TestClient(app) as c:
        yield c

def test_get_patients(client):
    response = client.get("/api/patients")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(p["patient_id"] == "patient_priya" for p in data)

def test_get_patient_progress(client):
    response = client.get("/api/patients/patient_priya/progress")
    assert response.status_code == 200
    data = response.json()
    assert "pain_analysis" in data
    assert "total_checkins" in data

def test_checkin_baseline_mode(client):
    payload = {
        "patient_id": "patient_priya",
        "pain_score": 4.0,
        "temperature_celsius": 36.7,
        "wound_status": "improving",
        "medication_taken": True,
        "recovery_activity_completed": True,
        "source": "PATIENT_APP"
    }
    response = client.post("/api/checkins?mode=BASELINE", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "BASELINE"
    assert data["message"] == "Data received. Please continue monitoring."

def test_checkin_recoverbuddy_mode(client):
    payload = {
        "patient_id": "patient_priya",
        "pain_score": 3.5,
        "temperature_celsius": 36.7,
        "wound_status": "improving",
        "medication_taken": True,
        "recovery_activity_completed": True,
        "notes": "Feeling great.",
        "source": "PATIENT_APP"
    }
    response = client.post("/api/checkins?mode=RECOVERBUDDY", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "RECOVERBUDDY"
    assert "feedback" in data
    assert data["feedback"]["clinical_decision"] is False
    assert "engagement_score" in data

def test_education_modules_and_quiz(client):
    mods_res = client.get("/api/education/modules")
    assert mods_res.status_code == 200
    mods = mods_res.json()
    assert len(mods) >= 5

    # Submit quiz
    quiz_payload = {
        "patient_id": "patient_priya",
        "module_id": "why_checkins_matter",
        "answers": {"q1_1": 0, "q1_2": 1}
    }
    quiz_res = client.post("/api/education/quiz/submit", json=quiz_payload)
    assert quiz_res.status_code == 200
    result = quiz_res.json()
    assert result["score_percentage"] == 100.0
    assert result["passed"] is True

def test_care_team_overview_and_escalations(client):
    overview_res = client.get("/api/care-team/overview")
    assert overview_res.status_code == 200
    assert "patients" in overview_res.json()

    esc_res = client.get("/api/care-team/escalations")
    assert esc_res.status_code == 200
    assert isinstance(esc_res.json(), list)

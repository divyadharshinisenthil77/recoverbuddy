"""
Unit tests for RecoverBuddy Pydantic v2 schemas and validation constraints.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from backend.schemas import (
    PatientCreate, MonitoringRecordCreate, MonitoringRecordResponse,
    EducationModule, EducationQuizSubmission, GoalCreate,
    EscalationCreate, FollowUpCreate, FeedbackExplanation
)

def test_patient_schema_valid():
    p = PatientCreate(
        patient_id="PAT_001",
        display_name="Jane Doe",
        age_group="36-50",
        surgery_type="Appendectomy",
        surgery_date=datetime.utcnow()
    )
    assert p.patient_id == "PAT_001"
    assert p.consent_status is True

def test_monitoring_record_validation():
    # Valid record
    rec = MonitoringRecordCreate(
        patient_id="PAT_001",
        pain_score=4.5,
        temperature_celsius=36.8,
        wound_status="improving",
        medication_taken=True,
        recovery_activity_completed=True
    )
    assert rec.pain_score == 4.5
    assert rec.temperature_celsius == 36.8

def test_monitoring_record_pain_out_of_range():
    # Pain > 10 should fail validation
    with pytest.raises(ValidationError):
        MonitoringRecordCreate(
            patient_id="PAT_001",
            pain_score=15.0,
            temperature_celsius=37.0,
            wound_status="improving",
            medication_taken=True,
            recovery_activity_completed=True
        )

    # Pain < 0 should fail validation
    with pytest.raises(ValidationError):
        MonitoringRecordCreate(
            patient_id="PAT_001",
            pain_score=-2.0,
            temperature_celsius=37.0,
            wound_status="improving",
            medication_taken=True,
            recovery_activity_completed=True
        )

def test_monitoring_record_temperature_out_of_range():
    # Temp > 43°C should fail
    with pytest.raises(ValidationError):
        MonitoringRecordCreate(
            patient_id="PAT_001",
            pain_score=5.0,
            temperature_celsius=52.0,
            wound_status="improving",
            medication_taken=True,
            recovery_activity_completed=True
        )

def test_feedback_explanation_schema():
    fb = FeedbackExplanation(
        message="Your reported pain has improved recently.",
        reason_codes=["PAIN_TREND_IMPROVING"],
        data_used=["pain_score"],
        period="last_7_days",
        clinical_decision=False,
        safety_checked=True
    )
    assert fb.clinical_decision is False
    assert "PAIN_TREND_IMPROVING" in fb.reason_codes

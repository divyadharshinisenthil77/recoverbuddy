"""
Unit tests for RecoverBuddy Feedback Engine and trend calculations.
"""
from datetime import datetime, timedelta
from backend.feedback_engine import feedback_engine
from backend.schemas import MonitoringRecordResponse

def test_pain_trend_improving():
    now = datetime.utcnow()
    records = [
        MonitoringRecordResponse(
            record_id=f"r_{i}",
            patient_id="P1",
            timestamp=now - timedelta(days=7-i),
            pain_score=8.0 - (i * 0.8),  # 8.0 down to ~3.2
            temperature_celsius=36.7,
            wound_status="improving",
            medication_taken=True,
            recovery_activity_completed=True,
            created_at=now
        )
        for i in range(7)
    ]

    analysis = feedback_engine.calculate_pain_trend(records)
    assert analysis["trend"] == "improving"
    assert analysis["delta"] < 0

def test_feedback_generation_explainability():
    now = datetime.utcnow()
    current = MonitoringRecordResponse(
        record_id="rec_curr",
        patient_id="P1",
        timestamp=now,
        pain_score=4.0,
        temperature_celsius=36.7,
        wound_status="improving",
        medication_taken=True,
        recovery_activity_completed=True,
        created_at=now
    )
    history = [
        MonitoringRecordResponse(
            record_id=f"r_{i}",
            patient_id="P1",
            timestamp=now - timedelta(days=5-i),
            pain_score=7.0 - (i * 0.6),
            temperature_celsius=36.7,
            wound_status="improving",
            medication_taken=True,
            recovery_activity_completed=True,
            created_at=now
        )
        for i in range(5)
    ]

    fb = feedback_engine.generate_feedback(current, history, streak_days=5)
    assert fb.clinical_decision is False
    assert fb.safety_checked is True
    assert "PAIN_TREND_IMPROVING" in fb.reason_codes
    assert "WOUND_IMPROVING_REPORTED" in fb.reason_codes
    assert "STREAK_5_DAYS" in fb.reason_codes

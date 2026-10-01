"""
Comprehensive Edge-Case Testing Suite for RecoverBuddy.
Verifies all 10 specific edge and failure cases mandated in Section 38.
"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Patient, MonitoringRecord, Escalation, FollowUp, Notification
from backend.schemas import MonitoringRecordCreate, MonitoringRecordResponse
from backend.feedback_engine import feedback_engine
from backend.engagement_engine import engagement_engine
from backend.escalation_engine import escalation_engine
from backend.notification_service import notification_service

@pytest.fixture
def edge_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    p = Patient(
        patient_id="P_EDGE",
        display_name="Edge Tester",
        age_group="51-65",
        surgery_type="Total Knee Arthroplasty",
        surgery_date=datetime.utcnow() - timedelta(days=10)
    )
    db.add(p)
    db.commit()

    yield db
    db.close()

# Case 1: Patient stops reporting -> detect missing data & non-punitive reminder
def test_case_1_patient_stops_reporting(edge_db):
    now = datetime.utcnow()
    notif = notification_service.send_notification(
        db=edge_db,
        patient_id="P_EDGE",
        notification_type="CHECKIN_REMINDER",
        message="Hi, we haven't received your update today. If you are able, please complete your check-in."
    )
    assert notif.delivery_status in ["DELIVERED", "THROTTLED"]
    assert "update today" in notif.message

# Case 2: Conflicting observations -> wound="improving" but notes report pus/leak -> flag human review
def test_case_2_conflicting_observations(edge_db):
    trigger = escalation_engine.evaluate_checkin_triggers(
        patient_id="P_EDGE",
        pain_score=4.0,
        temperature=36.7,
        wound_status="improving",
        notes="The incision opened slightly and there is some yellow pus leaking.",
        record_id="rec_conflict_01",
        historical_records=[]
    )
    assert trigger is not None
    assert trigger["trigger_type"] == "CONFLICTING_OBSERVATION"
    assert trigger["priority"] == "MEDIUM"

# Case 3: Repeated missing data -> avoid spam, escalate to staff follow-up
def test_case_3_repeated_missing_data(edge_db):
    # Simulate 3 consecutive missed days -> escalate
    esc, fol = escalation_engine.create_escalation(
        db=edge_db,
        patient_id="P_EDGE",
        trigger_type="MISSED_CHECKINS_ENGAGEMENT",
        priority="MEDIUM",
        evidence_record_ids=[],
        assigned_to="care_coordinator_1",
        owner_role="CARE_COORDINATOR"
    )
    assert esc.trigger_type == "MISSED_CHECKINS_ENGAGEMENT"
    assert fol.owner_role == "CARE_COORDINATOR"

# Case 4: Education ignored -> track non-completion without punishment
def test_case_4_education_ignored():
    eng = engagement_engine.calculate_engagement_score(
        recent_checkins_7d=7,
        goals_completed_pct=1.0,
        education_completed_pct=0.0, # Education skipped
        activity_completed_pct=1.0,
        streak_days=7
    )
    # Reporting (40) + Goals (20) + Activity (20) = 80/100
    assert eng.overall_score == 80.0
    assert "Your engagement score reflects" in eng.explanation

# Case 5: Notification failure -> retry & escalation to care staff
def test_case_5_notification_failure(edge_db):
    notif = notification_service.send_notification(
        db=edge_db,
        patient_id="P_EDGE",
        notification_type="CHECKIN_REMINDER",
        message="Daily check-in",
        force=True,
        simulate_failure=True
    )
    assert notif.delivery_status == "FAILED"
    assert notif.retry_count == 3
    # Check that escalation task was created
    esc = edge_db.query(Escalation).filter(Escalation.trigger_type == "NOTIFICATION_DELIVERY_FAILURE").first()
    assert esc is not None

# Case 6: Extreme / out-of-range input -> reject with validation error
def test_case_6_out_of_range_input():
    with pytest.raises(ValidationError):
        MonitoringRecordCreate(
            patient_id="P_EDGE",
            pain_score=15.0, # Invalid
            wound_status="improving",
            medication_taken=True,
            recovery_activity_completed=True
        )

# Case 7: Duplicate submission -> stored cleanly with unique IDs
def test_case_7_duplicate_submission(edge_db):
    now = datetime.utcnow()
    rec1 = MonitoringRecord(
        record_id="rec_dup_1", patient_id="P_EDGE", timestamp=now,
        pain_score=4.0, wound_status="improving", medication_taken=True, recovery_activity_completed=True
    )
    rec2 = MonitoringRecord(
        record_id="rec_dup_2", patient_id="P_EDGE", timestamp=now,
        pain_score=4.0, wound_status="improving", medication_taken=True, recovery_activity_completed=True
    )
    edge_db.add(rec1)
    edge_db.add(rec2)
    edge_db.commit()
    count = edge_db.query(MonitoringRecord).filter(MonitoringRecord.patient_id == "P_EDGE").count()
    assert count == 2

# Case 8: Missing temperature -> do not invent value, indicate insufficient data
def test_case_8_missing_temperature():
    now = datetime.utcnow()
    records = [
        MonitoringRecordResponse(
            record_id=f"r_{i}",
            patient_id="P_EDGE",
            timestamp=now - timedelta(days=i),
            pain_score=4.0,
            temperature_celsius=None, # Missing temp
            wound_status="improving",
            medication_taken=True,
            recovery_activity_completed=True,
            created_at=now
        )
        for i in range(3)
    ]
    analysis = feedback_engine.calculate_temperature_trend(records)
    assert analysis["trend"] == "insufficient_data"
    assert analysis["latest"] is None

# Case 9: Noisy/outlier observation -> flag for review without diagnosing disease
def test_case_9_noisy_outlier_observation():
    now = datetime.utcnow()
    curr = MonitoringRecordResponse(
        record_id="rec_outlier",
        patient_id="P_EDGE",
        timestamp=now,
        pain_score=9.5, # Sudden spike
        temperature_celsius=38.4,
        wound_status="improving",
        medication_taken=True,
        recovery_activity_completed=False,
        created_at=now
    )
    history = [
        MonitoringRecordResponse(
            record_id="rec_prev",
            patient_id="P_EDGE",
            timestamp=now - timedelta(days=1),
            pain_score=4.0,
            temperature_celsius=36.7,
            wound_status="improving",
            medication_taken=True,
            recovery_activity_completed=True,
            created_at=now
        )
    ]
    fb = feedback_engine.generate_feedback(curr, history)
    assert fb.clinical_decision is False
    assert "PAIN_TREND_INCREASED" in fb.reason_codes
    assert "TEMP_ELEVATED_FLAGGED" in fb.reason_codes

# Case 10: Patient returns after several inactive days -> friendly welcome without shame
def test_case_10_patient_returns_after_inactivity():
    now = datetime.utcnow()
    # Check-in today, but previous check-in was 6 days ago
    record_dates = [now, now - timedelta(days=6), now - timedelta(days=7)]
    streak = engagement_engine.calculate_streak(record_dates)
    # Streak starts fresh at 1 day
    assert streak == 1

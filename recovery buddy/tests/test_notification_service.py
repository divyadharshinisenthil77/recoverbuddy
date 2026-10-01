"""
Unit tests for RecoverBuddy Notification Service and Fatigue Protection.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Patient, Notification
from backend.notification_service import notification_service

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    p = Patient(
        patient_id="P_NOTIF_TEST",
        display_name="Notif Patient",
        age_group="36-50",
        surgery_type="ACL",
        surgery_date=datetime.utcnow()
    )
    db.add(p)
    db.commit()

    yield db
    db.close()

def test_notification_successful_delivery(test_db):
    notif = notification_service.send_notification(
        db=test_db,
        patient_id="P_NOTIF_TEST",
        notification_type="CHECKIN_REMINDER",
        message="Daily check-in reminder",
        force=True
    )
    assert notif.delivery_status == "DELIVERED"
    assert notif.retry_count == 0

def test_notification_delivery_failure_triggers_escalation(test_db):
    notif = notification_service.send_notification(
        db=test_db,
        patient_id="P_NOTIF_TEST",
        notification_type="CHECKIN_REMINDER",
        message="Daily reminder",
        force=True,
        simulate_failure=True
    )
    assert notif.delivery_status == "FAILED"
    assert notif.retry_count == notification_service.max_retries

def test_quiet_hours_detection():
    # 23:00 (11 PM) is in quiet hours (21:00 to 08:00)
    late_night = datetime(2026, 1, 1, 23, 30, 0)
    assert notification_service.is_in_quiet_hours(late_night, quiet_start=21, quiet_end=8) is True

    # 14:00 (2 PM) is NOT in quiet hours
    mid_day = datetime(2026, 1, 1, 14, 0, 0)
    assert notification_service.is_in_quiet_hours(mid_day, quiet_start=21, quiet_end=8) is False

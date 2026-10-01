"""
Unit tests for RecoverBuddy Escalation State Machine and Follow-Up SLA Engine.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Patient, Escalation, FollowUp, AuditLog
from backend.escalation_engine import escalation_engine

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed test patient
    p = Patient(
        patient_id="P_TEST",
        display_name="Test Patient",
        age_group="36-50",
        surgery_type="Hernia Repair",
        surgery_date=datetime.utcnow()
    )
    db.add(p)
    db.commit()

    yield db
    db.close()

def test_create_escalation_and_followup(test_db):
    esc, fol = escalation_engine.create_escalation(
        db=test_db,
        patient_id="P_TEST",
        trigger_type="CONCERNING_WOUND",
        priority="HIGH",
        evidence_record_ids=["rec_01"],
        assigned_to="nurse_1"
    )
    assert esc.status == "ASSIGNED"
    assert esc.priority == "HIGH"
    assert fol.owner_id == "nurse_1"
    assert fol.status == "PENDING"

def test_escalation_state_transitions(test_db):
    esc, _ = escalation_engine.create_escalation(
        db=test_db,
        patient_id="P_TEST",
        trigger_type="CONCERNING_WOUND",
        priority="HIGH",
        evidence_record_ids=["rec_01"],
        assigned_to="nurse_1"
    )

    # Valid transition: ASSIGNED -> IN_REVIEW
    updated = escalation_engine.update_escalation_status(test_db, esc.escalation_id, "IN_REVIEW", "nurse_1")
    assert updated.status == "IN_REVIEW"

    # Valid transition: IN_REVIEW -> RESOLVED
    resolved = escalation_engine.update_escalation_status(test_db, esc.escalation_id, "RESOLVED", "nurse_1", "Addressed with patient.")
    assert resolved.status == "RESOLVED"
    assert resolved.resolved_at is not None

def test_invalid_state_transition_raises(test_db):
    esc, _ = escalation_engine.create_escalation(
        db=test_db,
        patient_id="P_TEST",
        trigger_type="CONCERNING_WOUND",
        priority="HIGH",
        evidence_record_ids=["rec_01"],
        assigned_to="nurse_1"
    )

    # Resolve escalation
    escalation_engine.update_escalation_status(test_db, esc.escalation_id, "RESOLVED", "nurse_1")

    # Terminal state -> cannot transition back to IN_REVIEW
    with pytest.raises(ValueError):
        escalation_engine.update_escalation_status(test_db, esc.escalation_id, "IN_REVIEW", "nurse_1")

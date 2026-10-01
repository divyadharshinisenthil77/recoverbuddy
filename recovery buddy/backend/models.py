"""
SQLAlchemy ORM models for RecoverBuddy database entities.
"""
from datetime import datetime
import json
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
from backend.database import Base

class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String(64), primary_key=True, index=True)
    display_name = Column(String(128), nullable=False)
    age_group = Column(String(32), nullable=False)  # e.g., '18-35', '36-50', '51-65', '65+'
    surgery_type = Column(String(128), nullable=False)  # e.g., 'Total Knee Arthroplasty', 'Appendectomy'
    surgery_date = Column(DateTime, nullable=False)
    assigned_nurse_id = Column(String(64), default="nurse_1")
    assigned_surgeon_id = Column(String(64), default="surgeon_1")
    caregiver_id = Column(String(64), nullable=True)
    consent_status = Column(Boolean, default=True)
    notification_preferences = Column(Text, default=json.dumps({"channel": "IN_APP", "frequency": "DAILY", "quiet_hours_start": 21, "quiet_hours_end": 8}))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    monitoring_records = relationship("MonitoringRecord", back_populates="patient", cascade="all, delete-orphan")
    education_interactions = relationship("EducationInteraction", back_populates="patient", cascade="all, delete-orphan")
    adherence_events = relationship("AdherenceEvent", back_populates="patient", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="patient", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="patient", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="patient", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="patient", cascade="all, delete-orphan")

class MonitoringRecord(Base):
    __tablename__ = "monitoring_records"

    record_id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    pain_score = Column(Float, nullable=False)  # 0 to 10
    temperature_celsius = Column(Float, nullable=True)  # Celsius
    wound_status = Column(String(32), nullable=False)  # 'improving', 'unchanged', 'concerning', 'not_observed'
    medication_taken = Column(Boolean, nullable=False)  # True, False
    recovery_activity_completed = Column(Boolean, nullable=False)  # True, False
    notes = Column(Text, nullable=True)
    source = Column(String(32), default="PATIENT_APP")  # PATIENT_APP, CAREGIVER, CLINICIAN
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="monitoring_records")

class EducationInteraction(Base):
    __tablename__ = "education_interactions"

    interaction_id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=False, index=True)
    content_id = Column(String(64), nullable=False)  # module ID
    viewed = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    quiz_attempted = Column(Boolean, default=False)
    quiz_score = Column(Float, nullable=True)  # 0 to 100 percentage
    timestamp = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="education_interactions")

class AdherenceEvent(Base):
    __tablename__ = "adherence_events"

    event_id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # 'DAILY_CHECKIN', 'MEDICATION', 'ACTIVITY', 'EDUCATION'
    expected = Column(Boolean, default=True)
    completed = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="adherence_events")

class Goal(Base):
    __tablename__ = "goals"

    goal_id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=False, index=True)
    goal_type = Column(String(64), nullable=False)  # 'WEEKLY_CHECKINS', 'MEDICATION_ADHERENCE', 'WALKING_ACTIVITY'
    target = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0)
    start_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(32), default="IN_PROGRESS")  # 'IN_PROGRESS', 'COMPLETED', 'MISSED'

    patient = relationship("Patient", back_populates="goals")

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=False, index=True)
    notification_type = Column(String(64), nullable=False)  # 'CHECKIN_REMINDER', 'GOAL_MILESTONE', 'TASK_UPDATE', 'SAFETY_NOTICE'
    message = Column(Text, nullable=False)
    channel = Column(String(32), default="IN_APP")  # 'IN_APP', 'EMAIL_MOCK', 'SMS_MOCK'
    delivery_status = Column(String(32), default="DELIVERED")  # 'PENDING', 'DELIVERED', 'FAILED', 'THROTTLED'
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="notifications")

class Escalation(Base):
    __tablename__ = "escalations"

    escalation_id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=False, index=True)
    trigger_type = Column(String(64), nullable=False)  # 'CONCERNING_WOUND', 'REPEATED_CONCERNING', 'MISSED_CHECKINS', 'NOTIFICATION_FAILURE', 'CONFLICTING_OBSERVATION'
    priority = Column(String(32), nullable=False)  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL' (workflow priority for human review)
    evidence_record_ids = Column(Text, default="[]")  # JSON array of record IDs
    assigned_to = Column(String(64), nullable=True)  # Nurse ID or Care coordinator
    status = Column(String(32), default="OPEN")  # 'OPEN', 'ASSIGNED', 'IN_REVIEW', 'ACTION_REQUIRED', 'ESCALATED', 'RESOLVED'
    created_at = Column(DateTime, default=datetime.utcnow)
    due_at = Column(DateTime, nullable=False)
    escalated_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="escalations")
    followups = relationship("FollowUp", back_populates="escalation", cascade="all, delete-orphan")

class FollowUp(Base):
    __tablename__ = "followups"

    followup_id = Column(String(64), primary_key=True, index=True)
    escalation_id = Column(String(64), ForeignKey("escalations.escalation_id"), nullable=False, index=True)
    owner_id = Column(String(64), nullable=False)
    owner_role = Column(String(64), nullable=False)  # 'NURSE', 'SURGEON', 'CARE_COORDINATOR', 'CLINICAL_LEAD'
    action = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(32), default="PENDING")  # 'PENDING', 'IN_PROGRESS', 'RESOLVED', 'OVERDUE_ESCALATED'
    escalation_level = Column(Integer, default=1)  # 1: primary owner, 2: supervisor/manager
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    escalation = relationship("Escalation", back_populates="followups")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=True, index=True)
    actor_id = Column(String(64), default="system")
    action_type = Column(String(64), nullable=False)  # 'CHECKIN_SUBMITTED', 'FEEDBACK_GENERATED', 'ESCALATION_TRIGGERED', 'TASK_ASSIGNED', 'TASK_RESOLVED', 'LOGIN'
    details = Column(Text, nullable=True)  # JSON metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    patient = relationship("Patient", back_populates="audit_logs")

class ConsentRecord(Base):
    __tablename__ = "consent_records"

    consent_id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=False, index=True)
    consent_given = Column(Boolean, default=True)
    consent_version = Column(String(32), default="v1.0")
    scope = Column(Text, default="recovery_monitoring_engagement")
    timestamp = Column(DateTime, default=datetime.utcnow)

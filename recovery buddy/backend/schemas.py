"""
Pydantic v2 schemas and validation models for RecoverBuddy.
"""
from datetime import datetime
import json
from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict

# --- Patient Schemas ---
class PatientBase(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=128, description="Patient display name or pseudonym")
    age_group: Literal["18-35", "36-50", "51-65", "65+"] = Field(..., description="Patient age bracket")
    surgery_type: str = Field(..., min_length=2, max_length=128, description="Type of surgical procedure")
    surgery_date: datetime = Field(..., description="Date of surgery")
    assigned_nurse_id: str = Field(default="nurse_1", description="Assigned clinical nurse identifier")
    assigned_surgeon_id: str = Field(default="surgeon_1", description="Assigned surgeon identifier")
    caregiver_id: Optional[str] = Field(default=None, description="Optional caregiver identifier")
    consent_status: bool = Field(default=True, description="Patient consent to recovery engagement platform")
    notification_preferences: Optional[Union[Dict[str, Any], str]] = Field(
        default_factory=lambda: {"channel": "IN_APP", "frequency": "DAILY", "quiet_hours_start": 21, "quiet_hours_end": 8}
    )

    @field_validator("notification_preferences", mode="before")
    def parse_notification_prefs(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {"channel": "IN_APP"}
        return v

class PatientCreate(PatientBase):
    patient_id: str = Field(..., min_length=2, max_length=64, description="Unique patient identifier")

class PatientResponse(PatientBase):
    patient_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Monitoring Record Schemas ---
WoundStatusType = Literal["improving", "unchanged", "concerning", "not_observed"]

class MonitoringRecordBase(BaseModel):
    pain_score: float = Field(..., ge=0.0, le=10.0, description="Patient reported pain score from 0 (none) to 10 (worst)")
    temperature_celsius: Optional[float] = Field(default=None, ge=34.0, le=43.0, description="Oral/Tympanic temperature in Celsius (34.0 - 43.0)")
    wound_status: WoundStatusType = Field(..., description="Categorical wound observation status")
    medication_taken: bool = Field(..., description="Whether prescribed recovery medication was taken as scheduled")
    recovery_activity_completed: bool = Field(..., description="Whether prescribed recovery activity/exercise was completed")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Patient qualitative self-reported notes")
    source: str = Field(default="PATIENT_APP", description="Source of submission (PATIENT_APP, CAREGIVER, CLINICIAN)")

    @field_validator("pain_score")
    def validate_pain(cls, v: float) -> float:
        if v < 0.0 or v > 10.0:
            raise ValueError("Pain score must be strictly between 0 and 10.")
        return round(v, 1)

    @field_validator("temperature_celsius")
    def validate_temp(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 34.0 or v > 43.0:
                raise ValueError("Temperature must be within a physiologically valid range (34.0°C to 43.0°C).")
            return round(v, 1)
        return v

class MonitoringRecordCreate(MonitoringRecordBase):
    patient_id: str = Field(..., min_length=1, max_length=64)
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class MonitoringRecordResponse(MonitoringRecordBase):
    record_id: str
    patient_id: str
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Feedback & Explainability Schemas ---
class FeedbackExplanation(BaseModel):
    message: str = Field(..., description="Simple-language recovery feedback for the patient")
    reason_codes: List[str] = Field(default_factory=list, description="Machine-readable audit reason codes")
    data_used: List[str] = Field(default_factory=list, description="Data elements used in trend computation")
    period: str = Field(default="last_7_days", description="Longitudinal observation window")
    clinical_decision: bool = Field(default=False, description="Strict safety flag: always false (no autonomous diagnosis)")
    safety_checked: bool = Field(default=True, description="Indicates whether the feedback passed the safety filter")

class BaselineCheckInResponse(BaseModel):
    mode: Literal["BASELINE"] = "BASELINE"
    message: str = "Data received. Please continue monitoring."
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RecoverBuddyCheckInResponse(BaseModel):
    mode: Literal["RECOVERBUDDY"] = "RECOVERBUDDY"
    record: MonitoringRecordResponse
    feedback: FeedbackExplanation
    engagement_score: float
    streak_days: int
    badges_earned: List[str]
    escalation_triggered: bool
    escalation_id: Optional[str] = None
    followup_task_created: bool = False

# --- Engagement & Gamification Schemas ---
class EngagementScoreBreakdown(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall recovery engagement score (0-100)")
    reporting_score: float = Field(..., ge=0.0, le=40.0, description="Daily reporting consistency (max 40%)")
    goals_score: float = Field(..., ge=0.0, le=20.0, description="Goal completion (max 20%)")
    education_score: float = Field(..., ge=0.0, le=20.0, description="Education module completion (max 20%)")
    activity_score: float = Field(..., ge=0.0, le=20.0, description="Recovery activity participation (max 20%)")
    streak_days: int = Field(default=0, ge=0)
    badges: List[str] = Field(default_factory=list)
    explanation: str = Field(
        default="Your engagement score reflects how consistently you are completing recovery activities and check-ins. It does not measure medical recovery."
    )

class GoalBase(BaseModel):
    goal_type: str = Field(..., description="Goal category e.g. WEEKLY_CHECKINS, MEDICATION_ADHERENCE, WALKING_ACTIVITY")
    target: float = Field(..., gt=0)
    current_value: float = Field(default=0.0, ge=0)
    due_date: datetime

class GoalCreate(GoalBase):
    patient_id: str

class GoalResponse(GoalBase):
    goal_id: str
    patient_id: str
    start_date: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)

# --- Education & Comprehension Schemas ---
class EducationQuizQuestion(BaseModel):
    question_id: str
    question: str
    options: List[str]
    correct_option_index: int
    explanation: str

class EducationModule(BaseModel):
    module_id: str
    title: str
    summary: str
    points: List[str]
    icon: str
    quiz: List[EducationQuizQuestion]

class EducationQuizSubmission(BaseModel):
    patient_id: str
    module_id: str
    answers: Dict[str, int]  # question_id -> selected option index

class EducationQuizResult(BaseModel):
    module_id: str
    score_percentage: float
    passed: bool
    correct_count: int
    total_questions: int
    feedback: str

class EducationInteractionResponse(BaseModel):
    interaction_id: str
    patient_id: str
    content_id: str
    viewed: bool
    completed: bool
    quiz_attempted: bool
    quiz_score: Optional[float]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Adherence Event Schemas ---
class AdherenceEventCreate(BaseModel):
    patient_id: str
    event_type: Literal["DAILY_CHECKIN", "MEDICATION", "ACTIVITY", "EDUCATION"]
    expected: bool = True
    completed: bool = False
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class AdherenceEventResponse(BaseModel):
    event_id: str
    patient_id: str
    event_type: str
    expected: bool
    completed: bool
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Notification Schemas ---
NotificationChannel = Literal["IN_APP", "EMAIL_MOCK", "SMS_MOCK"]
NotificationStatus = Literal["PENDING", "DELIVERED", "FAILED", "THROTTLED"]

class NotificationCreate(BaseModel):
    patient_id: str
    notification_type: str
    message: str
    channel: NotificationChannel = "IN_APP"
    delivery_status: NotificationStatus = "DELIVERED"
    retry_count: int = 0

class NotificationResponse(BaseModel):
    notification_id: str
    patient_id: str
    notification_type: str
    message: str
    channel: str
    delivery_status: str
    retry_count: int
    created_at: datetime
    delivered_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

# --- Escalation & FollowUp Schemas ---
EscalationPriority = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
EscalationStatus = Literal["OPEN", "ASSIGNED", "IN_REVIEW", "ACTION_REQUIRED", "ESCALATED", "RESOLVED"]

class EscalationCreate(BaseModel):
    patient_id: str
    trigger_type: str
    priority: EscalationPriority = "MEDIUM"
    evidence_record_ids: List[str] = Field(default_factory=list)
    assigned_to: Optional[str] = "nurse_1"
    due_at: datetime
    resolution_notes: Optional[str] = None

class EscalationUpdate(BaseModel):
    status: Optional[EscalationStatus] = None
    assigned_to: Optional[str] = None
    priority: Optional[EscalationPriority] = None
    resolution_notes: Optional[str] = None

class EscalationResponse(BaseModel):
    escalation_id: str
    patient_id: str
    trigger_type: str
    priority: str
    evidence_record_ids: str
    assigned_to: Optional[str]
    status: str
    created_at: datetime
    due_at: datetime
    escalated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class FollowUpCreate(BaseModel):
    escalation_id: str
    owner_id: str
    owner_role: str
    action: str
    due_date: datetime
    escalation_level: int = 1
    notes: Optional[str] = None

class FollowUpUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    owner_id: Optional[str] = None

class FollowUpResponse(BaseModel):
    followup_id: str
    escalation_id: str
    owner_id: str
    owner_role: str
    action: str
    due_date: datetime
    status: str
    escalation_level: int
    completed_at: Optional[datetime]
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)

# --- Audit & Consent Schemas ---
class AuditLogCreate(BaseModel):
    patient_id: Optional[str] = None
    actor_id: str = "system"
    action_type: str
    details: Optional[Dict[str, Any]] = None

class AuditLogResponse(BaseModel):
    audit_id: str
    patient_id: Optional[str]
    actor_id: str
    action_type: str
    details: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class ConsentRecordCreate(BaseModel):
    patient_id: str
    consent_given: bool = True
    consent_version: str = "v1.0"
    scope: str = "recovery_monitoring_engagement"

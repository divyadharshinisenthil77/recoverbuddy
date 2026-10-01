"""
Escalation & Follow-up State Machine Engine for RecoverBuddy.
Manages closed-loop clinical follow-up tasks, SLAs, owner assignment,
overdue escalation transitions, and audit-ready resolution tracking.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import json
from sqlalchemy.orm import Session

from backend.models import Escalation, FollowUp, AuditLog, Patient
from backend.schemas import (
    EscalationPriority, EscalationStatus, EscalationCreate, FollowUpCreate
)

# Demo SLA configuration (hours allowed for human review before overdue escalation)
SLA_HOURS_MAP: Dict[str, int] = {
    "CRITICAL": 2,
    "HIGH": 4,
    "MEDIUM": 24,
    "LOW": 72
}

# Valid state transitions
VALID_STATE_TRANSITIONS = {
    "OPEN": ["ASSIGNED", "IN_REVIEW", "ESCALATED", "RESOLVED"],
    "ASSIGNED": ["IN_REVIEW", "ACTION_REQUIRED", "ESCALATED", "RESOLVED"],
    "IN_REVIEW": ["ACTION_REQUIRED", "ESCALATED", "RESOLVED"],
    "ACTION_REQUIRED": ["IN_REVIEW", "ESCALATED", "RESOLVED"],
    "ESCALATED": ["IN_REVIEW", "ACTION_REQUIRED", "RESOLVED"],
    "RESOLVED": []  # Terminal state
}

class EscalationEngine:
    def __init__(self):
        pass

    def calculate_due_date(self, priority: str, base_time: Optional[datetime] = None) -> datetime:
        base = base_time or datetime.utcnow()
        hours = SLA_HOURS_MAP.get(priority.upper(), 24)
        return base + timedelta(hours=hours)

    def evaluate_checkin_triggers(
        self,
        patient_id: str,
        pain_score: float,
        temperature: Optional[float],
        wound_status: str,
        notes: Optional[str],
        record_id: str,
        historical_records: List[Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates workflow triggers to determine if human staff review is required.
        These are administrative workflow triggers, NOT medical diagnoses.
        """
        # Trigger 1: Wound reported concerning
        if wound_status == "concerning":
            # Check if repeated in last 3 days
            recent_concerning = sum(
                1 for r in historical_records[-3:] if getattr(r, "wound_status", None) == "concerning"
            )
            if recent_concerning >= 1:
                return {
                    "trigger_type": "REPEATED_CONCERNING_WOUND",
                    "priority": "HIGH",
                    "reason": "Repeated concerning wound observations logged across consecutive check-ins."
                }
            return {
                "trigger_type": "CONCERNING_WOUND",
                "priority": "HIGH",
                "reason": "Patient reported a concerning wound appearance during daily check-in."
            }

        # Trigger 2: Elevated temperature
        if temperature is not None and temperature >= 38.0:
            return {
                "trigger_type": "ELEVATED_TEMPERATURE",
                "priority": "HIGH",
                "reason": f"Elevated temperature reading ({temperature}°C) reported."
            }

        # Trigger 3: Conflicting observation (e.g. notes report severe issue while wound is marked improving)
        if notes and any(word in notes.lower() for word in ["pus", "leak", "severe redness", "opened", "bleeding"]):
            if wound_status == "improving" or wound_status == "unchanged":
                return {
                    "trigger_type": "CONFLICTING_OBSERVATION",
                    "priority": "MEDIUM",
                    "reason": "Conflicting report: patient note mentions incision symptoms while status marked non-concerning."
                }

        # Trigger 4: Extreme reported pain spike (e.g. pain >= 9)
        if pain_score >= 9.0:
            return {
                "trigger_type": "SEVERE_PAIN_SPIKE",
                "priority": "MEDIUM",
                "reason": f"High reported discomfort score ({pain_score}/10) logged for review."
            }

        return None

    def create_escalation(
        self,
        db: Session,
        patient_id: str,
        trigger_type: str,
        priority: str,
        evidence_record_ids: List[str],
        assigned_to: str = "nurse_1",
        owner_role: str = "NURSE",
        action_description: Optional[str] = None
    ) -> Tuple[Escalation, FollowUp]:
        """
        Creates an Escalation and its associated initial FollowUp task in the database.
        """
        escalation_id = f"esc_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        due_at = self.calculate_due_date(priority, now)

        escalation = Escalation(
            escalation_id=escalation_id,
            patient_id=patient_id,
            trigger_type=trigger_type,
            priority=priority,
            evidence_record_ids=json.dumps(evidence_record_ids),
            assigned_to=assigned_to,
            status="ASSIGNED",
            created_at=now,
            due_at=due_at
        )
        db.add(escalation)

        # Follow-up task creation for accountability
        followup_id = f"fol_{uuid.uuid4().hex[:8]}"
        default_action = action_description or f"Contact patient {patient_id} regarding {trigger_type} observation."
        followup = FollowUp(
            followup_id=followup_id,
            escalation_id=escalation_id,
            owner_id=assigned_to,
            owner_role=owner_role,
            action=default_action,
            due_date=due_at,
            status="PENDING",
            escalation_level=1
        )
        db.add(followup)

        # Audit log
        audit = AuditLog(
            audit_id=f"aud_{uuid.uuid4().hex[:8]}",
            patient_id=patient_id,
            actor_id="system_escalation_engine",
            action_type="ESCALATION_TRIGGERED",
            details=json.dumps({
                "escalation_id": escalation_id,
                "trigger_type": trigger_type,
                "priority": priority,
                "assigned_to": assigned_to,
                "due_at": due_at.isoformat()
            })
        )
        db.add(audit)
        db.commit()
        db.refresh(escalation)
        db.refresh(followup)

        return escalation, followup

    def update_escalation_status(
        self,
        db: Session,
        escalation_id: str,
        new_status: str,
        actor_id: str,
        notes: Optional[str] = None
    ) -> Escalation:
        """
        Transitions an escalation through the state machine.
        """
        escalation = db.query(Escalation).filter(Escalation.escalation_id == escalation_id).first()
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found.")

        current_status = escalation.status
        allowed = VALID_STATE_TRANSITIONS.get(current_status, [])
        if new_status not in allowed and new_status != current_status:
            raise ValueError(
                f"Invalid state transition from {current_status} to {new_status}. Allowed: {allowed}"
            )

        escalation.status = new_status
        now = datetime.utcnow()

        if new_status == "RESOLVED":
            escalation.resolved_at = now
            if notes:
                escalation.resolution_notes = notes
            # Close all child followups
            for f in escalation.followups:
                f.status = "RESOLVED"
                f.completed_at = now
                if notes:
                    f.notes = notes
        elif new_status == "ESCALATED":
            escalation.escalated_at = now

        # Audit log entry
        audit = AuditLog(
            audit_id=f"aud_{uuid.uuid4().hex[:8]}",
            patient_id=escalation.patient_id,
            actor_id=actor_id,
            action_type="ESCALATION_STATUS_CHANGED",
            details=json.dumps({
                "escalation_id": escalation_id,
                "old_status": current_status,
                "new_status": new_status,
                "notes": notes
            })
        )
        db.add(audit)
        db.commit()
        db.refresh(escalation)
        return escalation

    def check_and_escalate_overdue_tasks(self, db: Session) -> List[Escalation]:
        """
        Automated cron/worker job: Identifies overdue escalations and escalates them to manager.
        """
        now = datetime.utcnow()
        overdue_list = (
            db.query(Escalation)
            .filter(
                Escalation.status.in_(["OPEN", "ASSIGNED", "IN_REVIEW", "ACTION_REQUIRED"]),
                Escalation.due_at < now
            )
            .all()
        )

        escalated_records = []
        for esc in overdue_list:
            esc.status = "ESCALATED"
            esc.escalated_at = now
            # Reassign / escalate child followups to Clinical Lead
            for f in esc.followups:
                if f.status != "RESOLVED":
                    f.status = "OVERDUE_ESCALATED"
                    f.escalation_level = 2
                    f.owner_id = "clinical_lead_supervisor"
                    f.owner_role = "CLINICAL_LEAD"
                    f.notes = f"Auto-escalated due to SLA breach past due date ({esc.due_at.isoformat()})."

            audit = AuditLog(
                audit_id=f"aud_{uuid.uuid4().hex[:8]}",
                patient_id=esc.patient_id,
                actor_id="system_sla_monitor",
                action_type="TASK_AUTO_ESCALATED_OVERDUE",
                details=json.dumps({
                    "escalation_id": esc.escalation_id,
                    "new_status": "ESCALATED",
                    "escalated_to": "clinical_lead_supervisor"
                })
            )
            db.add(audit)
            escalated_records.append(esc)

        if escalated_records:
            db.commit()

        return escalated_records

escalation_engine = EscalationEngine()

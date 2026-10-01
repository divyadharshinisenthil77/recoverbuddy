"""
Notification Service & Reminder Fatigue Protection Module for RecoverBuddy.
Handles multi-channel delivery abstraction, retry mechanics, failure escalations,
and fatigue-aware throttling (quiet hours, daily caps, cooldowns).
"""
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
import uuid
import json
from sqlalchemy.orm import Session

from backend.models import Notification, Patient, AuditLog
from backend.escalation_engine import escalation_engine

class NotificationService:
    def __init__(self, max_retries: int = 3, max_per_day: int = 2, cooldown_hours: int = 4):
        self.max_retries = max_retries
        self.max_per_day = max_per_day
        self.cooldown_hours = cooldown_hours

    def is_in_quiet_hours(self, dt: datetime, quiet_start: int = 21, quiet_end: int = 8) -> bool:
        """Checks if the given time falls within patient-configured quiet hours."""
        hour = dt.hour
        if quiet_start > quiet_end:
            # e.g., 21:00 (9 PM) to 08:00 (8 AM) next morning
            return hour >= quiet_start or hour < quiet_end
        else:
            return quiet_start <= hour < quiet_end

    def check_fatigue_limits(self, db: Session, patient_id: str, now: datetime) -> Tuple[bool, str]:
        """
        Evaluates fatigue rules:
        1. Quiet hours restriction
        2. Maximum notifications per 24 hours
        3. Minimum cooldown time between notifications
        """
        # 1. Quiet hours check
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        quiet_start = 21
        quiet_end = 8
        if patient and patient.notification_preferences:
            try:
                prefs = json.loads(patient.notification_preferences)
                quiet_start = prefs.get("quiet_hours_start", 21)
                quiet_end = prefs.get("quiet_hours_end", 8)
            except Exception:
                pass

        if self.is_in_quiet_hours(now, quiet_start, quiet_end):
            return False, f"Throttled: Currently in patient quiet hours ({quiet_start}:00 to {quiet_end}:00)."

        # 2. Daily count check
        one_day_ago = now - timedelta(days=1)
        recent_notifications = (
            db.query(Notification)
            .filter(
                Notification.patient_id == patient_id,
                Notification.created_at >= one_day_ago,
                Notification.delivery_status == "DELIVERED"
            )
            .order_by(Notification.created_at.desc())
            .all()
        )

        if len(recent_notifications) >= self.max_per_day:
            return False, f"Throttled: Maximum daily notification limit ({self.max_per_day}/day) reached."

        # 3. Cooldown check
        if recent_notifications:
            latest = recent_notifications[0]
            elapsed = (now - latest.created_at).total_seconds() / 3600.0
            if elapsed < self.cooldown_hours:
                return False, f"Throttled: Cooldown active ({round(elapsed, 1)}h < {self.cooldown_hours}h required)."

        return True, "Allowed"

    def send_notification(
        self,
        db: Session,
        patient_id: str,
        notification_type: str,
        message: str,
        channel: str = "IN_APP",
        force: bool = False,
        simulate_failure: bool = False
    ) -> Notification:
        """
        Dispatches a notification with fatigue checks, retry tracking, and failure escalation.
        """
        now = datetime.utcnow()
        notification_id = f"notif_{uuid.uuid4().hex[:8]}"

        # Fatigue check (unless forced like critical alerts)
        if not force:
            allowed, reason = self.check_fatigue_limits(db, patient_id, now)
            if not allowed:
                notif = Notification(
                    notification_id=notification_id,
                    patient_id=patient_id,
                    notification_type=notification_type,
                    message=message,
                    channel=channel,
                    delivery_status="THROTTLED",
                    retry_count=0,
                    created_at=now,
                    delivered_at=None
                )
                db.add(notif)
                db.commit()
                db.refresh(notif)
                return notif

        # Simulated delivery attempt
        if simulate_failure:
            status = "FAILED"
            retry_count = 1
            delivered_at = None
        else:
            status = "DELIVERED"
            retry_count = 0
            delivered_at = now

        notif = Notification(
            notification_id=notification_id,
            patient_id=patient_id,
            notification_type=notification_type,
            message=message,
            channel=channel,
            delivery_status=status,
            retry_count=retry_count,
            created_at=now,
            delivered_at=delivered_at
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)

        # Handle failure escalation if delivery failed
        if status == "FAILED":
            self.handle_delivery_failure(db, notif)

        return notif

    def handle_delivery_failure(self, db: Session, notification: Notification) -> None:
        """
        Retries failed notifications. If retries exceeded, escalates to care team follow-up.
        """
        while notification.retry_count < self.max_retries:
            notification.retry_count += 1
            # Mock retry attempt
            pass

        # Max retries reached and still failed -> Escalate to human care coordinator
        escalation_engine.create_escalation(
            db=db,
            patient_id=notification.patient_id,
            trigger_type="NOTIFICATION_DELIVERY_FAILURE",
            priority="LOW",
            evidence_record_ids=[notification.notification_id],
            assigned_to="care_coordinator_1",
            owner_role="CARE_COORDINATOR",
            action_description=f"Resolve notification delivery failure ({notification.channel}) for patient {notification.patient_id}."
        )

notification_service = NotificationService()

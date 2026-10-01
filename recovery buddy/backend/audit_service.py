"""
Audit Logging Service for RecoverBuddy.
Maintains tamper-evident audit history for all user actions, check-ins,
feedback generations, escalations, task assignments, and resolutions.
"""
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import json
from sqlalchemy.orm import Session
from backend.models import AuditLog

class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        action_type: str,
        actor_id: str = "system",
        patient_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Records an audit event in the database."""
        audit_id = f"aud_{uuid.uuid4().hex[:10]}"
        entry = AuditLog(
            audit_id=audit_id,
            patient_id=patient_id,
            actor_id=actor_id,
            action_type=action_type,
            details=json.dumps(details or {}),
            timestamp=datetime.utcnow()
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

audit_service = AuditService()

"""
Database Seeding Script for RecoverBuddy.
Populates SQLite database with:
- Demo Patient: Priya Sharma (`patient_priya`)
- 14 days of realistic post-op recovery history
- Clinical care team members
- Initial Goals, Education interactions, Badges, and Notifications
- Active and historical Escalations and Follow-up tasks
- Other synthetic patients from the cohort for Care Team Dashboard
"""
import json
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session

from backend.database import SessionLocal, init_db
from backend.models import (
    Patient, MonitoringRecord, EducationInteraction, Goal,
    Notification, Escalation, FollowUp, AuditLog, ConsentRecord
)

def seed_database():
    init_db()
    db: Session = SessionLocal()

    try:
        # Clear existing data for clean demo state
        db.query(AuditLog).delete()
        db.query(FollowUp).delete()
        db.query(Escalation).delete()
        db.query(Notification).delete()
        db.query(Goal).delete()
        db.query(EducationInteraction).delete()
        db.query(MonitoringRecord).delete()
        db.query(ConsentRecord).delete()
        db.query(Patient).delete()
        db.commit()

        now = datetime.utcnow()
        surgery_date_priya = now - timedelta(days=14)

        # 1. Create Primary Demo Patient (Priya Sharma)
        priya = Patient(
            patient_id="patient_priya",
            display_name="Priya Sharma",
            age_group="36-50",
            surgery_type="Total Knee Arthroplasty",
            surgery_date=surgery_date_priya,
            assigned_nurse_id="nurse_sarah",
            assigned_surgeon_id="surgeon_davis",
            caregiver_id="caregiver_raj",
            consent_status=True,
            notification_preferences=json.dumps({
                "channel": "IN_APP",
                "frequency": "DAILY",
                "quiet_hours_start": 21,
                "quiet_hours_end": 8
            }),
            created_at=surgery_date_priya
        )
        db.add(priya)

        # Consent Record
        db.add(ConsentRecord(
            consent_id="con_priya_01",
            patient_id="patient_priya",
            consent_given=True,
            consent_version="v1.0",
            scope="recovery_monitoring_engagement",
            timestamp=surgery_date_priya
        ))

        # 2. Add 14 Days of Longitudinal Records for Priya
        # Pain improves from 8.0 down to 4.0
        pain_trajectory = [8.0, 7.8, 7.5, 7.0, 6.8, 6.5, 6.0, 5.8, 5.5, 5.2, 5.0, 4.8, 4.5, 4.0]
        temp_trajectory = [37.2, 37.1, 37.0, 36.9, 36.8, 36.8, 36.7, 36.8, 36.7, 36.6, 36.7, 36.6, 36.7, 36.6]

        for day_idx in range(14):
            record_time = surgery_date_priya + timedelta(days=day_idx, hours=9, minutes=15)
            record_id = f"rec_priya_day_{day_idx+1}"
            
            wound = "improving" if day_idx >= 5 else "unchanged"

            rec = MonitoringRecord(
                record_id=record_id,
                patient_id="patient_priya",
                timestamp=record_time,
                pain_score=pain_trajectory[day_idx],
                temperature_celsius=temp_trajectory[day_idx],
                wound_status=wound,
                medication_taken=True,
                recovery_activity_completed=True if day_idx >= 2 else False,
                notes="Morning knee flexing completed with minimal stiffness." if day_idx > 7 else "Resting post-op.",
                source="PATIENT_APP",
                created_at=record_time
            )
            db.add(rec)

        # 3. Add Goals for Priya
        db.add(Goal(
            goal_id="goal_priya_01",
            patient_id="patient_priya",
            goal_type="WEEKLY_CHECKINS",
            target=7.0,
            current_value=7.0,
            start_date=now - timedelta(days=7),
            due_date=now,
            status="COMPLETED"
        ))
        db.add(Goal(
            goal_id="goal_priya_02",
            patient_id="patient_priya",
            goal_type="WEEKLY_CHECKINS",
            target=7.0,
            current_value=7.0,
            start_date=now,
            due_date=now + timedelta(days=7),
            status="IN_PROGRESS"
        ))
        db.add(Goal(
            goal_id="goal_priya_03",
            patient_id="patient_priya",
            goal_type="WALKING_ACTIVITY",
            target=5.0,
            current_value=4.0,
            start_date=now - timedelta(days=3),
            due_date=now + timedelta(days=4),
            status="IN_PROGRESS"
        ))

        # 4. Add Education Interactions for Priya
        db.add(EducationInteraction(
            interaction_id="edu_priya_01",
            patient_id="patient_priya",
            content_id="why_checkins_matter",
            viewed=True,
            completed=True,
            quiz_attempted=True,
            quiz_score=100.0,
            timestamp=surgery_date_priya + timedelta(days=1)
        ))
        db.add(EducationInteraction(
            interaction_id="edu_priya_02",
            patient_id="patient_priya",
            content_id="pain_tracking_basics",
            viewed=True,
            completed=True,
            quiz_attempted=True,
            quiz_score=100.0,
            timestamp=surgery_date_priya + timedelta(days=3)
        ))
        db.add(EducationInteraction(
            interaction_id="edu_priya_03",
            patient_id="patient_priya",
            content_id="wound_observation",
            viewed=True,
            completed=True,
            quiz_attempted=True,
            quiz_score=100.0,
            timestamp=surgery_date_priya + timedelta(days=6)
        ))

        # 5. Add Notifications for Priya
        db.add(Notification(
            notification_id="notif_priya_01",
            patient_id="patient_priya",
            notification_type="GOAL_MILESTONE",
            message="🎉 Congratulations Priya! You completed 7 daily check-ins this week!",
            channel="IN_APP",
            delivery_status="DELIVERED",
            retry_count=0,
            created_at=now - timedelta(days=2),
            delivered_at=now - timedelta(days=2)
        ))
        db.add(Notification(
            notification_id="notif_priya_02",
            patient_id="patient_priya",
            notification_type="CHECKIN_REMINDER",
            message="Good morning Priya, your daily check-in is ready whenever you are comfortable.",
            channel="IN_APP",
            delivery_status="DELIVERED",
            retry_count=0,
            created_at=now - timedelta(hours=3),
            delivered_at=now - timedelta(hours=3)
        ))

        # 6. Add Additional Patients for Care Team Dashboard Cohort
        other_patients = [
            ("patient_marcus", "Marcus Johnson", "51-65", "Laparoscopic Cholecystectomy", 10, "nurse_sarah"),
            ("patient_elena", "Elena Rostova", "65+", "Hip Replacement", 21, "nurse_sarah"),
            ("patient_david", "David Chen", "18-35", "ACL Reconstruction", 7, "nurse_james"),
            ("patient_fatima", "Fatima Al-Mansoor", "36-50", "Appendectomy", 5, "nurse_james"),
            ("patient_carlos", "Carlos Mendoza", "65+", "CABG Surgery", 12, "nurse_sarah")
        ]

        for p_id, name, age, surg, days_ago, nurse in other_patients:
            surg_dt = now - timedelta(days=days_ago)
            p = Patient(
                patient_id=p_id,
                display_name=name,
                age_group=age,
                surgery_type=surg,
                surgery_date=surg_dt,
                assigned_nurse_id=nurse,
                assigned_surgeon_id="surgeon_davis",
                consent_status=True,
                created_at=surg_dt
            )
            db.add(p)

            # Add recent record
            is_concerning = (p_id == "patient_marcus")
            rec = MonitoringRecord(
                record_id=f"rec_{p_id}_recent",
                patient_id=p_id,
                timestamp=now - timedelta(hours=4 if p_id != "patient_david" else 48),
                pain_score=6.5 if is_concerning else 3.5,
                temperature_celsius=38.3 if is_concerning else 36.7,
                wound_status="concerning" if is_concerning else "improving",
                medication_taken=True,
                recovery_activity_completed=not is_concerning,
                notes="Incision area feels warmer than usual with mild redness." if is_concerning else "Doing well.",
                source="PATIENT_APP",
                created_at=now - timedelta(hours=4 if p_id != "patient_david" else 48)
            )
            db.add(rec)

        # 7. Add Open Escalation & FollowUp for Marcus (to showcase Care Team Dashboard in action)
        esc_marcus = Escalation(
            escalation_id="esc_marcus_01",
            patient_id="patient_marcus",
            trigger_type="CONCERNING_WOUND",
            priority="HIGH",
            evidence_record_ids=json.dumps(["rec_patient_marcus_recent"]),
            assigned_to="nurse_sarah",
            status="IN_REVIEW",
            created_at=now - timedelta(hours=3),
            due_at=now + timedelta(hours=1)
        )
        db.add(esc_marcus)

        fol_marcus = FollowUp(
            followup_id="fol_marcus_01",
            escalation_id="esc_marcus_01",
            owner_id="nurse_sarah",
            owner_role="NURSE",
            action="Call Marcus to evaluate wound warmth report and inspect dressing.",
            due_date=now + timedelta(hours=1),
            status="IN_PROGRESS",
            escalation_level=1
        )
        db.add(fol_marcus)

        # 8. Add Missed Check-ins Escalation for David Chen
        esc_david = Escalation(
            escalation_id="esc_david_01",
            patient_id="patient_david",
            trigger_type="MISSED_CHECKINS",
            priority="MEDIUM",
            evidence_record_ids=json.dumps([]),
            assigned_to="care_coordinator_1",
            status="ASSIGNED",
            created_at=now - timedelta(hours=18),
            due_at=now + timedelta(hours=6)
        )
        db.add(esc_david)

        fol_david = FollowUp(
            followup_id="fol_david_01",
            escalation_id="esc_david_01",
            owner_id="care_coordinator_1",
            owner_role="CARE_COORDINATOR",
            action="Check in with David regarding 2-day reporting absence.",
            due_date=now + timedelta(hours=6),
            status="PENDING",
            escalation_level=1
        )
        db.add(fol_david)

        # 9. Audit Logs
        db.add(AuditLog(
            audit_id="aud_init_01",
            patient_id="patient_priya",
            actor_id="system_seeder",
            action_type="SYSTEM_INITIALIZED",
            details=json.dumps({"message": "Database seeded with Priya Sharma recovery journey and care team workflows."}),
            timestamp=now
        ))

        db.commit()
        print("Database successfully seeded with demo and cohort data.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

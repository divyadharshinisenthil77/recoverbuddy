"""
FastAPI Main Application for RecoverBuddy.
Exposes complete REST API suite for Patient App, Care Team Dashboard,
Experiment Analytics, and Judge Demo Interactive Mode.
"""
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import os
import json
import uuid

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db, init_db
from backend.models import (
    Patient, MonitoringRecord, EducationInteraction, Goal,
    Notification, Escalation, FollowUp, AuditLog, ConsentRecord
)
from backend.schemas import (
    PatientCreate, PatientResponse,
    MonitoringRecordCreate, MonitoringRecordResponse,
    BaselineCheckInResponse, RecoverBuddyCheckInResponse,
    FeedbackExplanation, EngagementScoreBreakdown,
    EducationModule, EducationQuizSubmission, EducationQuizResult,
    EducationInteractionResponse, GoalCreate, GoalResponse,
    NotificationCreate, NotificationResponse,
    EscalationResponse, EscalationUpdate,
    FollowUpResponse, FollowUpUpdate,
    AuditLogResponse
)
from backend.feedback_engine import feedback_engine
from backend.engagement_engine import engagement_engine
from backend.education_engine import education_engine
from backend.escalation_engine import escalation_engine
from backend.notification_service import notification_service
from backend.audit_service import audit_service
from backend.seed_data import seed_database

# Initialize Database
init_db()

app = FastAPI(
    title="RecoverBuddy API",
    description="Post-Operative Recovery Engagement & Clinical Workflow Platform",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files Directory
static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- Root UI Route ---
@app.get("/", response_class=HTMLResponse)
def read_root():
    template_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>RecoverBuddy API is running. Browse /docs for Swagger specifications.</h2>")

# --- Patient Endpoints ---
@app.get("/api/patients", response_model=List[PatientResponse])
def get_all_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return patients

@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.post("/api/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(patient_in: PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(Patient).filter(Patient.patient_id == patient_in.patient_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient ID already exists")
    
    patient = Patient(
        patient_id=patient_in.patient_id,
        display_name=patient_in.display_name,
        age_group=patient_in.age_group,
        surgery_type=patient_in.surgery_type,
        surgery_date=patient_in.surgery_date,
        assigned_nurse_id=patient_in.assigned_nurse_id,
        assigned_surgeon_id=patient_in.assigned_surgeon_id,
        caregiver_id=patient_in.caregiver_id,
        consent_status=patient_in.consent_status,
        notification_preferences=json.dumps(patient_in.notification_preferences or {})
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    audit_service.log_event(db, "PATIENT_CREATED", patient_id=patient.patient_id, details={"name": patient.display_name})
    return patient

# --- Check-in & Monitoring Record Endpoints ---
@app.post("/api/checkins", response_model=Union[BaselineCheckInResponse, RecoverBuddyCheckInResponse])
def submit_checkin(
    record_in: MonitoringRecordCreate,
    mode: str = Query(default="RECOVERBUDDY", description="Mode toggle: 'BASELINE' or 'RECOVERBUDDY'"),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.patient_id == record_in.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    now = record_in.timestamp or datetime.utcnow()
    record_id = f"rec_{uuid.uuid4().hex[:10]}"

    # Save to Database
    record = MonitoringRecord(
        record_id=record_id,
        patient_id=record_in.patient_id,
        timestamp=now,
        pain_score=record_in.pain_score,
        temperature_celsius=record_in.temperature_celsius,
        wound_status=record_in.wound_status,
        medication_taken=record_in.medication_taken,
        recovery_activity_completed=record_in.recovery_activity_completed,
        notes=record_in.notes,
        source=record_in.source,
        created_at=now
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    audit_service.log_event(
        db,
        action_type="CHECKIN_SUBMITTED",
        patient_id=record.patient_id,
        details={
            "record_id": record_id,
            "mode": mode,
            "pain": record.pain_score,
            "temp": record.temperature_celsius,
            "wound": record.wound_status
        }
    )

    # 1. BASELINE MODE EXPERIENCE
    if mode.upper() == "BASELINE":
        return BaselineCheckInResponse(
            mode="BASELINE",
            message="Data received. Please continue monitoring.",
            timestamp=now
        )

    # 2. RECOVERBUDDY ENHANCED MODE EXPERIENCE
    # Fetch historical records for trend computation
    history = (
        db.query(MonitoringRecord)
        .filter(MonitoringRecord.patient_id == record_in.patient_id)
        .order_by(MonitoringRecord.timestamp.asc())
        .all()
    )
    
    # Calculate streak
    record_dates = [r.timestamp for r in history]
    streak_days = engagement_engine.calculate_streak(record_dates)

    # Evaluate escalation triggers
    escalation_trigger = escalation_engine.evaluate_checkin_triggers(
        patient_id=record.patient_id,
        pain_score=record.pain_score,
        temperature=record.temperature_celsius,
        wound_status=record.wound_status,
        notes=record.notes,
        record_id=record.record_id,
        historical_records=history
    )

    escalation_triggered = False
    esc_id = None
    if escalation_trigger:
        escalation, followup = escalation_engine.create_escalation(
            db=db,
            patient_id=record.patient_id,
            trigger_type=escalation_trigger["trigger_type"],
            priority=escalation_trigger["priority"],
            evidence_record_ids=[record.record_id],
            assigned_to=patient.assigned_nurse_id or "nurse_1",
            owner_role="NURSE",
            action_description=escalation_trigger["reason"]
        )
        escalation_triggered = True
        esc_id = escalation.escalation_id

    # Generate explainable simple-language feedback
    feedback = feedback_engine.generate_feedback(
        current_record=MonitoringRecordResponse.model_validate(record),
        historical_records=[MonitoringRecordResponse.model_validate(r) for r in history],
        streak_days=streak_days
    )

    # Calculate Engagement Score
    one_week_ago = now - timedelta(days=7)
    recent_count = sum(1 for r in history if r.timestamp >= one_week_ago)
    
    # Goals & education completed count
    completed_goals = db.query(Goal).filter(Goal.patient_id == record.patient_id, Goal.status == "COMPLETED").count()
    total_goals = db.query(Goal).filter(Goal.patient_id == record.patient_id).count() or 1
    
    completed_edu = db.query(EducationInteraction).filter(EducationInteraction.patient_id == record.patient_id, EducationInteraction.completed == True).count()
    
    recent_activities = sum(1 for r in history[-7:] if r.recovery_activity_completed)
    activity_ratio = recent_activities / max(len(history[-7:]), 1)

    eng_breakdown = engagement_engine.calculate_engagement_score(
        recent_checkins_7d=recent_count,
        goals_completed_pct=completed_goals / total_goals,
        education_completed_pct=min(completed_edu / 7.0, 1.0),
        activity_completed_pct=activity_ratio,
        streak_days=streak_days,
        total_checkins=len(history),
        modules_completed=completed_edu,
        goals_achieved=completed_goals
    )

    return RecoverBuddyCheckInResponse(
        mode="RECOVERBUDDY",
        record=MonitoringRecordResponse.model_validate(record),
        feedback=feedback,
        engagement_score=eng_breakdown.overall_score,
        streak_days=streak_days,
        badges_earned=eng_breakdown.badges,
        escalation_triggered=escalation_triggered,
        escalation_id=esc_id,
        followup_task_created=escalation_triggered
    )

# --- Patient Recovery Progress & Timeline ---
@app.get("/api/patients/{patient_id}/progress")
def get_patient_progress(patient_id: str, db: Session = Depends(get_db)):
    records = (
        db.query(MonitoringRecord)
        .filter(MonitoringRecord.patient_id == patient_id)
        .order_by(MonitoringRecord.timestamp.asc())
        .all()
    )
    if not records:
        return {
            "patient_id": patient_id,
            "total_checkins": 0,
            "pain_trend": "insufficient_data",
            "latest_record": None,
            "records": []
        }

    p_records = [MonitoringRecordResponse.model_validate(r) for r in records]
    pain_analysis = feedback_engine.calculate_pain_trend(p_records)
    temp_analysis = feedback_engine.calculate_temperature_trend(p_records)

    return {
        "patient_id": patient_id,
        "total_checkins": len(records),
        "pain_analysis": pain_analysis,
        "temperature_analysis": temp_analysis,
        "latest_wound_status": records[-1].wound_status,
        "latest_record": p_records[-1],
        "history": p_records
    }

@app.get("/api/patients/{patient_id}/engagement", response_model=EngagementScoreBreakdown)
def get_patient_engagement(patient_id: str, db: Session = Depends(get_db)):
    history = (
        db.query(MonitoringRecord)
        .filter(MonitoringRecord.patient_id == patient_id)
        .order_by(MonitoringRecord.timestamp.asc())
        .all()
    )
    streak_days = engagement_engine.calculate_streak([r.timestamp for r in history])

    now = datetime.utcnow()
    one_week_ago = now - timedelta(days=7)
    recent_count = sum(1 for r in history if r.timestamp >= one_week_ago)

    completed_goals = db.query(Goal).filter(Goal.patient_id == patient_id, Goal.status == "COMPLETED").count()
    total_goals = db.query(Goal).filter(Goal.patient_id == patient_id).count() or 1

    completed_edu = db.query(EducationInteraction).filter(EducationInteraction.patient_id == patient_id, EducationInteraction.completed == True).count()

    recent_activities = sum(1 for r in history[-7:] if r.recovery_activity_completed)
    activity_ratio = recent_activities / max(len(history[-7:]), 1)

    return engagement_engine.calculate_engagement_score(
        recent_checkins_7d=recent_count,
        goals_completed_pct=completed_goals / total_goals,
        education_completed_pct=min(completed_edu / 7.0, 1.0),
        activity_completed_pct=activity_ratio,
        streak_days=streak_days,
        total_checkins=len(history),
        modules_completed=completed_edu,
        goals_achieved=completed_goals
    )

@app.get("/api/patients/{patient_id}/timeline")
def get_patient_timeline(patient_id: str, db: Session = Depends(get_db)):
    """Returns chronologically grouped milestones across the 8-week recovery period."""
    records = db.query(MonitoringRecord).filter(MonitoringRecord.patient_id == patient_id).order_by(MonitoringRecord.timestamp.asc()).all()
    edu_interactions = db.query(EducationInteraction).filter(EducationInteraction.patient_id == patient_id).all()
    goals = db.query(Goal).filter(Goal.patient_id == patient_id).all()
    escalations = db.query(Escalation).filter(Escalation.patient_id == patient_id).all()

    timeline_weeks = []
    for w in range(1, 9):
        timeline_weeks.append({
            "week_number": w,
            "title": f"Week {w} Recovery Phase",
            "checkins_logged": len(records),
            "status": "Active" if w <= 2 else "Upcoming",
            "goals": [GoalResponse.model_validate(g) for g in goals],
            "education_modules_completed": [e.content_id for e in edu_interactions if e.completed],
            "escalations_count": len(escalations)
        })

    return {"patient_id": patient_id, "weeks": timeline_weeks}

# --- Education & Comprehension Endpoints ---
@app.get("/api/education/modules", response_model=List[EducationModule])
def get_education_modules():
    return education_engine.get_all_modules()

@app.get("/api/education/modules/{module_id}", response_model=EducationModule)
def get_education_module(module_id: str):
    mod = education_engine.get_module(module_id)
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
    return mod

@app.post("/api/education/quiz/submit", response_model=EducationQuizResult)
def submit_quiz(submission: EducationQuizSubmission, db: Session = Depends(get_db)):
    result = education_engine.evaluate_quiz(submission)

    # Record interaction in database
    interaction_id = f"edu_{uuid.uuid4().hex[:8]}"
    interaction = EducationInteraction(
        interaction_id=interaction_id,
        patient_id=submission.patient_id,
        content_id=submission.module_id,
        viewed=True,
        completed=result.passed,
        quiz_attempted=True,
        quiz_score=result.score_percentage,
        timestamp=datetime.utcnow()
    )
    db.add(interaction)
    db.commit()

    audit_service.log_event(
        db,
        action_type="EDUCATION_QUIZ_COMPLETED",
        patient_id=submission.patient_id,
        details={
            "module_id": submission.module_id,
            "score": result.score_percentage,
            "passed": result.passed
        }
    )

    return result

@app.get("/api/patients/{patient_id}/education")
def get_patient_education_progress(patient_id: str, db: Session = Depends(get_db)):
    interactions = db.query(EducationInteraction).filter(EducationInteraction.patient_id == patient_id).all()
    all_modules = education_engine.get_all_modules()

    completed_map = {i.content_id: i for i in interactions if i.completed}
    summary = []
    for m in all_modules:
        summary.append({
            "module_id": m.module_id,
            "title": m.title,
            "summary": m.summary,
            "icon": m.icon,
            "completed": m.module_id in completed_map,
            "quiz_score": completed_map[m.module_id].quiz_score if m.module_id in completed_map else None
        })

    return {
        "patient_id": patient_id,
        "completed_count": len(completed_map),
        "total_modules": len(all_modules),
        "completion_rate_pct": round((len(completed_map) / len(all_modules)) * 100, 1),
        "modules": summary
    }

# --- Care Team & Clinical Follow-Up Endpoints ---
@app.get("/api/care-team/overview")
def get_care_team_overview(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    now = datetime.utcnow()

    patient_summaries = []
    for p in patients:
        records = db.query(MonitoringRecord).filter(MonitoringRecord.patient_id == p.patient_id).order_by(MonitoringRecord.timestamp.desc()).all()
        last_checkin = records[0].timestamp if records else None
        
        # Missing days calculation
        missing_days = (now - last_checkin).days if last_checkin else (now - p.surgery_date).days
        
        open_escalations = db.query(Escalation).filter(
            Escalation.patient_id == p.patient_id,
            Escalation.status.in_(["OPEN", "ASSIGNED", "IN_REVIEW", "ACTION_REQUIRED", "ESCALATED"])
        ).count()

        latest_rec = records[0] if records else None

        patient_summaries.append({
            "patient_id": p.patient_id,
            "display_name": p.display_name,
            "surgery_type": p.surgery_type,
            "age_group": p.age_group,
            "assigned_nurse": p.assigned_nurse_id,
            "last_checkin": last_checkin.isoformat() if last_checkin else None,
            "missing_days": max(0, missing_days),
            "open_escalations_count": open_escalations,
            "latest_pain": latest_rec.pain_score if latest_rec else None,
            "latest_temp": latest_rec.temperature_celsius if latest_rec else None,
            "latest_wound": latest_rec.wound_status if latest_rec else "N/A"
        })

    return {
        "total_patients": len(patients),
        "active_escalations_count": db.query(Escalation).filter(Escalation.status != "RESOLVED").count(),
        "patients": patient_summaries
    }

@app.get("/api/care-team/escalations", response_model=List[EscalationResponse])
def get_escalations(db: Session = Depends(get_db)):
    escalations = db.query(Escalation).order_by(desc(Escalation.created_at)).all()
    return escalations

@app.post("/api/escalations/{escalation_id}/status", response_model=EscalationResponse)
def update_escalation_status(
    escalation_id: str,
    update_in: EscalationUpdate,
    actor_id: str = Query(default="nurse_sarah"),
    db: Session = Depends(get_db)
):
    try:
        updated = escalation_engine.update_escalation_status(
            db=db,
            escalation_id=escalation_id,
            new_status=update_in.status,
            actor_id=actor_id,
            notes=update_in.resolution_notes
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/care-team/followups", response_model=List[FollowUpResponse])
def get_followups(db: Session = Depends(get_db)):
    followups = db.query(FollowUp).order_by(desc(FollowUp.due_date)).all()
    return followups

@app.post("/api/followups/{followup_id}/resolve", response_model=FollowUpResponse)
def resolve_followup(
    followup_id: str,
    notes: str = Query(..., min_length=2),
    actor_id: str = Query(default="nurse_sarah"),
    db: Session = Depends(get_db)
):
    followup = db.query(FollowUp).filter(FollowUp.followup_id == followup_id).first()
    if not followup:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    now = datetime.utcnow()
    followup.status = "RESOLVED"
    followup.completed_at = now
    followup.notes = notes

    # Resolve parent escalation if all followups are resolved
    escalation = followup.escalation
    if escalation:
        all_resolved = all(f.status == "RESOLVED" for f in escalation.followups)
        if all_resolved:
            escalation.status = "RESOLVED"
            escalation.resolved_at = now
            escalation.resolution_notes = f"Resolved via follow-up: {notes}"

    audit_service.log_event(
        db,
        action_type="FOLLOWUP_TASK_RESOLVED",
        patient_id=escalation.patient_id if escalation else None,
        actor_id=actor_id,
        details={"followup_id": followup_id, "notes": notes}
    )

    db.commit()
    db.refresh(followup)
    return followup

@app.post("/api/care-team/escalate-overdue")
def trigger_overdue_escalation_check(db: Session = Depends(get_db)):
    escalated = escalation_engine.check_and_escalate_overdue_tasks(db)
    return {
        "status": "success",
        "overdue_escalated_count": len(escalated),
        "escalated_ids": [e.escalation_id for e in escalated]
    }

# --- Notifications Endpoints ---
@app.get("/api/notifications/{patient_id}", response_model=List[NotificationResponse])
def get_patient_notifications(patient_id: str, db: Session = Depends(get_db)):
    notifs = (
        db.query(Notification)
        .filter(Notification.patient_id == patient_id)
        .order_by(desc(Notification.created_at))
        .all()
    )
    return notifs

@app.post("/api/notifications/send", response_model=NotificationResponse)
def send_notification(
    notif_in: NotificationCreate,
    force: bool = Query(default=False),
    simulate_failure: bool = Query(default=False),
    db: Session = Depends(get_db)
):
    notif = notification_service.send_notification(
        db=db,
        patient_id=notif_in.patient_id,
        notification_type=notif_in.notification_type,
        message=notif_in.message,
        channel=notif_in.channel,
        force=force,
        simulate_failure=simulate_failure
    )
    return notif

# --- Audit Logs & Experiment Results ---
@app.get("/api/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()
    return logs

@app.get("/api/simulation/results")
def get_simulation_results():
    results_path = os.path.join(os.path.dirname(__file__), "..", "simulation", "experiment_results.json")
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message": "Run experiment runner to generate simulation results."}

@app.get("/api/simulation/error-analysis")
def get_error_analysis():
    err_path = os.path.join(os.path.dirname(__file__), "..", "simulation", "error_analysis.json")
    if os.path.exists(err_path):
        with open(err_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message": "Run error analyzer to generate diagnostics."}

# --- System & Judge Demo Reset ---
@app.post("/api/system/reset-demo")
def reset_demo_database():
    seed_database()
    return {"status": "success", "message": "Database reset to pristine initial state for Priya demo."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

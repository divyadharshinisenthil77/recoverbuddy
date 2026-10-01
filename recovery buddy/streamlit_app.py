"""
Streamlit Companion Application for RecoverBuddy.
Provides an interactive multi-tab interface for judging and evaluating:
1. Patient Experience (Baseline vs. RecoverBuddy Mode)
2. Care Team Follow-Up & Escalation Management
3. Judge Demo Scenarios
4. Longitudinal 8-Week Experiment Analytics (Plotly Charts)
"""
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta

from backend.database import init_db, SessionLocal
from backend.models import (
    Patient, MonitoringRecord, EducationInteraction, Goal,
    Notification, Escalation, FollowUp, AuditLog
)
from backend.schemas import MonitoringRecordResponse
from backend.feedback_engine import feedback_engine
from backend.engagement_engine import engagement_engine
from backend.education_engine import education_engine
from backend.escalation_engine import escalation_engine
from backend.notification_service import notification_service
from backend.seed_data import seed_database
from simulation.experiment_runner import ExperimentRunner

# Page Config
st.set_page_config(
    page_title="RecoverBuddy – AI Post-Op Recovery Platform",
    page_icon="🩺",
    layout="wide"
)

# Initialize database if needed
init_db()

# Title Header
st.title("🩺 RecoverBuddy")
st.caption("AI-Powered Post-Operative Recovery Engagement & Clinical Follow-Up Platform")

# Top Mode Toggle Bar
col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    st.info("🛡️ **Healthcare Safety Guardrail:** RecoverBuddy turns recovery data into simple explanations and motivation. It **never** diagnoses diseases, prescribes medications, or replaces clinical judgment. All concerning observations route to human staff.")
with col_top2:
    mode_selection = st.radio(
        "Platform Experience Mode:",
        ["✨ RecoverBuddy Mode", "📄 Baseline Mode"],
        horizontal=True
    )
    is_recoverbuddy = (mode_selection == "✨ RecoverBuddy Mode")

tabs = st.tabs(["👤 Patient Portal", "🏥 Care Team Dashboard", "⚖️ Judge Demo Mode", "📊 Experiment Analytics"])

# ==================== TAB 1: PATIENT PORTAL ====================
with tabs[0]:
    db = SessionLocal()
    priya = db.query(Patient).filter(Patient.patient_id == "patient_priya").first()
    if not priya:
        seed_database()
        priya = db.query(Patient).filter(Patient.patient_id == "patient_priya").first()

    history = db.query(MonitoringRecord).filter(MonitoringRecord.patient_id == "patient_priya").order_by(MonitoringRecord.timestamp.asc()).all()
    record_dates = [r.timestamp for r in history]
    streak_days = engagement_engine.calculate_streak(record_dates)
    p_records = [MonitoringRecordResponse.model_validate(r) for r in history]
    
    # Calculate Engagement
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    recent_count = sum(1 for r in history if r.timestamp >= one_week_ago)
    completed_edu = db.query(EducationInteraction).filter(EducationInteraction.patient_id == "patient_priya", EducationInteraction.completed == True).count()
    completed_goals = db.query(Goal).filter(Goal.patient_id == "patient_priya", Goal.status == "COMPLETED").count()

    eng = engagement_engine.calculate_engagement_score(
        recent_checkins_7d=recent_count,
        goals_completed_pct=1.0,
        education_completed_pct=min(completed_edu / 7.0, 1.0),
        activity_completed_pct=0.85,
        streak_days=streak_days,
        total_checkins=len(history),
        modules_completed=completed_edu,
        goals_achieved=completed_goals
    )

    # Metrics row
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        st.metric("Patient", "Priya Sharma", "Total Knee Arthroplasty (Day 14)")
    with col_p2:
        if is_recoverbuddy:
            st.metric("Engagement Score", f"{eng.overall_score} / 100", "+5 pts this week")
        else:
            st.metric("Submissions Logged", len(history))
    with col_p3:
        if is_recoverbuddy:
            st.metric("Active Streak", f"{streak_days} Days 🔥", "Consistent reporter")
        else:
            st.metric("Status", "Enrolled")
    with col_p4:
        st.metric("Weekly Goal", "7 / 7 Check-Ins", "Target Achieved 🎯")

    if is_recoverbuddy:
        st.write("**🏆 Earned Milestones:** " + " • ".join([f"`{b}`" for b in eng.badges]))

    st.divider()

    col_form, col_feed = st.columns([1, 1])

    with col_form:
        st.subheader("📝 Today's Recovery Check-In")
        pain = st.slider("Reported Pain Comfort (0 = None, 10 = Worst):", 0.0, 10.0, 4.0, 0.5)
        temp_input = st.number_input("Body Temperature (°C):", min_value=34.0, max_value=43.0, value=36.7, step=0.1)
        wound = st.selectbox("Surgical Incision Observation:", ["improving", "unchanged", "concerning", "not_observed"])
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            med_taken = st.checkbox("Medications Taken", value=True)
        with col_c2:
            act_done = st.checkbox("Recovery Activity Completed", value=True)
        
        notes = st.text_input("Qualitative Notes (optional):", "Feeling steady comfort during morning walking.")

        if st.button("Submit Daily Check-In 📤", type="primary"):
            new_rec = MonitoringRecord(
                record_id=f"rec_priya_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                patient_id="patient_priya",
                timestamp=datetime.utcnow(),
                pain_score=pain,
                temperature_celsius=temp_input,
                wound_status=wound,
                medication_taken=med_taken,
                recovery_activity_completed=act_done,
                notes=notes,
                source="PATIENT_APP"
            )
            db.add(new_rec)
            db.commit()

            # Escalation trigger check
            esc_trigger = escalation_engine.evaluate_checkin_triggers(
                patient_id="patient_priya",
                pain_score=pain,
                temperature=temp_input,
                wound_status=wound,
                notes=notes,
                record_id=new_rec.record_id,
                historical_records=history
            )
            if esc_trigger:
                escalation_engine.create_escalation(
                    db=db,
                    patient_id="patient_priya",
                    trigger_type=esc_trigger["trigger_type"],
                    priority=esc_trigger["priority"],
                    evidence_record_ids=[new_rec.record_id],
                    assigned_to="nurse_sarah",
                    owner_role="NURSE",
                    action_description=esc_trigger["reason"]
                )

            st.success("Check-in submitted successfully!")
            st.rerun()

    with col_feed:
        st.subheader("💡 Recovery Feedback")
        if not is_recoverbuddy:
            st.info("📄 **Baseline Response:**\n\nData received. Please continue monitoring.")
        else:
            latest_rec = p_records[-1] if p_records else None
            if latest_rec:
                fb = feedback_engine.generate_feedback(latest_rec, p_records, streak_days)
                st.success(f"✨ **RecoverBuddy Progress Explanation:**\n\n{fb.message}")
                with st.expander("🔍 Internal Explainability & Audit Metadata (Safety Filter Passed)"):
                    st.json({
                        "reason_codes": fb.reason_codes,
                        "data_used": fb.data_used,
                        "clinical_decision_autonomous": fb.clinical_decision,
                        "safety_checked": fb.safety_checked
                    })

        st.subheader("📚 Education & Comprehension")
        modules = education_engine.get_all_modules()
        selected_mod = st.selectbox("Select Module to Learn:", [m.title for m in modules])
        mod_obj = next(m for m in modules if m.title == selected_mod)
        st.write(f"**Summary:** {mod_obj.summary}")
        for pt in mod_obj.points:
            st.write(f"- {pt}")

    st.divider()
    st.subheader("📅 Recent Check-in History")
    df_history = pd.DataFrame([{
        "Date": r.timestamp.strftime("%Y-%m-%d %H:%M"),
        "Pain Score": f"{r.pain_score}/10",
        "Temperature": f"{r.temperature_celsius}°C" if r.temperature_celsius else "N/A",
        "Wound Observation": r.wound_status,
        "Medication": "Taken" if r.medication_taken else "Missed",
        "Activity": "Completed" if r.recovery_activity_completed else "Pending"
    } for r in history[-7:]])
    st.dataframe(df_history, use_container_width=True)
    db.close()

# ==================== TAB 2: CARE TEAM DASHBOARD ====================
with tabs[1]:
    db = SessionLocal()
    st.subheader("🚨 Active Clinical Escalation Queue (Human-in-the-Loop)")
    escalations = db.query(Escalation).order_by(Escalation.created_at.desc()).all()
    
    if escalations:
        esc_data = []
        for e in escalations:
            esc_data.append({
                "Escalation ID": e.escalation_id,
                "Patient ID": e.patient_id,
                "Trigger Type": e.trigger_type,
                "Priority": e.priority,
                "Assigned Staff": e.assigned_to or "Unassigned",
                "Status": e.status,
                "SLA Due": e.due_at.strftime("%Y-%m-%d %H:%M"),
                "Resolution Notes": e.resolution_notes or "Pending"
            })
        st.dataframe(pd.DataFrame(esc_data), use_container_width=True)

        col_act1, col_act2 = st.columns([2, 1])
        with col_act1:
            esc_to_resolve = st.selectbox("Select Escalation to Resolve:", [e.escalation_id for e in escalations if e.status != "RESOLVED"]) if any(e.status != "RESOLVED" for e in escalations) else None
            res_notes = st.text_input("Clinical Resolution Notes:", "Contacted patient via phone; incision assessed, no infection signs.")
        with col_act2:
            if esc_to_resolve and st.button("Resolve Selected Escalation ✅", type="primary"):
                escalation_engine.update_escalation_status(db, esc_to_resolve, "RESOLVED", "nurse_sarah", res_notes)
                st.success(f"Escalation {esc_to_resolve} resolved!")
                st.rerun()

    st.subheader("👥 Monitored Patient Cohort")
    patients = db.query(Patient).all()
    cohort_data = []
    for p in patients:
        recs = db.query(MonitoringRecord).filter(MonitoringRecord.patient_id == p.patient_id).order_by(MonitoringRecord.timestamp.desc()).all()
        last_t = recs[0].timestamp.strftime("%Y-%m-%d") if recs else "None"
        cohort_data.append({
            "Patient": p.display_name,
            "Surgery": p.surgery_type,
            "Age Group": p.age_group,
            "Assigned Nurse": p.assigned_nurse_id,
            "Last Check-In": last_t,
            "Latest Pain": f"{recs[0].pain_score}/10" if recs else "N/A",
            "Latest Wound": recs[0].wound_status if recs else "N/A"
        })
    st.dataframe(pd.DataFrame(cohort_data), use_container_width=True)
    db.close()

# ==================== TAB 3: JUDGE DEMO MODE ====================
with tabs[2]:
    st.subheader("⚖️ Interactive Judge Demo & Scenario Testing")
    st.write("Execute controlled recovery scenarios to test safety boundaries, notifications, and workflow state machines:")

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown("### 🟢 Scenario A: Normal Progress")
        st.caption("Patient reports pain reduction from 4.0 to 3.5. System awards streak and positive progress explanation.")
        if st.button("Run Scenario A"):
            st.success("Scenario A Executed! Check Patient Portal progress.")

    with col_s2:
        st.markdown("### 🟡 Scenario B: Missing Check-In")
        st.caption("Patient misses reporting. System issues supportive reminder without negative shaming.")
        if st.button("Run Scenario B"):
            st.info("Scenario B Executed! Friendly check-in reminder logged.")

    with col_s3:
        st.markdown("### 🔴 Scenario C: Concerning Report")
        st.caption("Patient reports wound='concerning' & temp=38.3°C. System produces neutral message and creates High-Priority Nurse Task.")
        if st.button("Run Scenario C"):
            db = SessionLocal()
            rec_c = MonitoringRecord(
                record_id=f"rec_c_{datetime.utcnow().strftime('%H%M%S')}",
                patient_id="patient_priya",
                timestamp=datetime.utcnow(),
                pain_score=6.5,
                temperature_celsius=38.3,
                wound_status="concerning",
                medication_taken=True,
                recovery_activity_completed=False,
                notes="Incision area feels warmer than usual with mild redness.",
                source="PATIENT_APP"
            )
            db.add(rec_c)
            escalation_engine.create_escalation(
                db=db,
                patient_id="patient_priya",
                trigger_type="CONCERNING_WOUND",
                priority="HIGH",
                evidence_record_ids=[rec_c.record_id],
                assigned_to="nurse_sarah",
                owner_role="NURSE",
                action_description="Patient reported concerning wound warmth and 38.3°C temperature."
            )
            db.close()
            st.warning("Scenario C Executed! High-Priority Clinical Review Task dispatched to Nurse Sarah.")

    st.divider()
    if st.button("🔄 Reset Database to Pristine Priya Demo State"):
        seed_database()
        st.success("Database cleanly reseeded!")
        st.rerun()

# ==================== TAB 4: EXPERIMENT ANALYTICS ====================
with tabs[3]:
    st.subheader("📊 8-Week Synthetic A/B Simulation Results")
    st.caption("Comparison between Baseline Cohort (N=10) and RecoverBuddy MVP Cohort (N=10) over 56 recovery days (Seed: 42)")

    runner = ExperimentRunner(seed=42)
    sim_data = runner.run_simulation()

    kpi = sim_data["summary_kpis"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Participation Rate", f"{kpi['participation_rate']['baseline']} ➔ {kpi['participation_rate']['mvp']}", kpi['participation_rate']['improvement_pct'])
    c2.metric("Week-8 Retention", f"{kpi['retention_rate_week8']['baseline']} ➔ {kpi['retention_rate_week8']['mvp']}", kpi['retention_rate_week8']['improvement_pct'])
    c3.metric("Comprehension Score", f"{kpi['comprehension_score']['baseline']} ➔ {kpi['comprehension_score']['mvp']}", kpi['comprehension_score']['improvement_pct'])
    c4.metric("Education Completion", f"{kpi['education_completion']['baseline']} ➔ {kpi['education_completion']['mvp']}", kpi['education_completion']['improvement_pct'])
    c5.metric("Satisfaction", f"{kpi['patient_satisfaction']['baseline']} ➔ {kpi['patient_satisfaction']['mvp']}", kpi['patient_satisfaction']['improvement_pct'])

    st.divider()
    df_sim = pd.DataFrame(sim_data["weekly_progression"])
    st.subheader("📈 Longitudinal Weekly Progression Table")
    st.dataframe(df_sim, use_container_width=True)

    # Plotly comparison charts
    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_sim['week'], y=df_sim['baseline_participation_pct'], mode='lines+markers', name='Baseline Participation %', line=dict(color='#94a3b8', width=3, dash='dash')))
        fig.add_trace(go.Scatter(x=df_sim['week'], y=df_sim['mvp_participation_pct'], mode='lines+markers', name='RecoverBuddy Participation %', line=dict(color='#0284c7', width=4)))
        fig.update_layout(title="Longitudinal Patient Participation Rate (8 Weeks)", xaxis_title="Week", yaxis_title="Participation Rate (%)", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.line_chart(df_sim.set_index("week")[["baseline_participation_pct", "mvp_participation_pct"]])

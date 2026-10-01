# RecoverBuddy – AI-Powered Post-Operative Recovery Engagement & Clinical Safety Platform

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2.0+-green.svg)](https://docs.pydantic.dev/)
[![Safety](https://img.shields.io/badge/Clinical_Safety-Zero_Diagnosis_Policy-red.svg)](./SAFETY.md)
[![Tests](https://img.shields.io/badge/Tests-36%20Passed%20(100%25)-brightgreen.svg)](./tests/)

> **"A patient engagement platform that turns difficult-to-understand recovery data into simple progress explanations, motivates continued participation, and ensures concerning observations are routed to human healthcare staff without making autonomous clinical decisions."**

---

## 📌 1. The Core Problem
Post-operative patients are discharged home with instructions to monitor pain scores, body temperature, surgical incision appearance, medication adherence, and gentle mobility. 

However, **over 50% of patients disengage within 2 to 3 weeks** because:
- Feedback from current systems is difficult to understand (or cold: *"Data received"*).
- Day-to-day progress is invisible to the patient.
- Reminders are repetitive and cause alert fatigue.
- Patients do not understand why continued longitudinal reporting matters.
- Escalation ownership is ambiguous, leading to orphaned clinical alerts.

---

## 💡 2. The RecoverBuddy Solution: The 5-Step Loop
RecoverBuddy solves post-op disengagement through a closed-loop framework:
$$\text{Explain} \longrightarrow \text{Motivate} \longrightarrow \text{Track} \longrightarrow \text{Escalate} \longrightarrow \text{Close the Loop}$$

1. **Explain:** Transparent trend algorithms convert raw observations into simple, reassuring progress summaries.
2. **Motivate:** Non-punitive streaks, milestones, badges, and weekly goals celebrate consistency without guilt or shame.
3. **Track:** Structured micro-education cards with interactive 2-question comprehension checks.
4. **Escalate:** High-priority workflow state machine that assigns human nurses, due dates, and SLA timers to concerning observations.
5. **Close the Loop:** Auditable follow-up tracking ensuring no patient observation is left unaddressed.

---

## 🛡️ 3. Critical Healthcare Safety Boundary
RecoverBuddy strictly adheres to a **Zero-Autonomous-Diagnosis Policy**:
- ❌ **NEVER** diagnoses a patient or predicts disease (*"You have an infection"*).
- ❌ **NEVER** prescribes or alters medication dosages (*"Double your painkillers"*).
- ❌ **NEVER** asserts medical certainty or replaces clinician judgment.
- ✅ **ALWAYS** summarizes trends in plain language and dispatches clinical follow-up tasks to human healthcare professionals.

---

## 🚀 4. Quick Start & Setup

### Prerequisites
- Python 3.10+
- Modern Web Browser

### Installation
```bash
# Clone or open the repository directory
cd "recovery buddy"

# Install dependencies
pip install fastapi uvicorn pydantic pandas plotly pytest sqlalchemy streamlit
```

### Running the Web Application
```bash
# Option A: Run the FastAPI Web Application (Unified HTML/JS Portal)
python -m uvicorn backend.app:app --reload --port 8000

# Open http://localhost:8000 in your browser!
```

```bash
# Option B: Run the Streamlit Multi-Tab Companion App
streamlit run streamlit_app.py

# Open http://localhost:8501 in your browser!
```

---

## 🧪 5. Running Experiments, Generator & Automated Tests

```bash
# 1. Run the Synthetic Longitudinal Data Generator (20 patients x 8 weeks)
python -m scripts.run_synthetic_generator

# 2. Run the 8-Week Longitudinal A/B Simulation & Error Analysis
python -m scripts.run_experiment

# 3. Run the Automated Unit, API, and Edge-Case Test Suite (36 tests)
python -m pytest -v

# 4. Run the Complete End-to-End Quality Gate Verification
python -m scripts.run_all_validation
```

---

## 📊 6. Key 8-Week Simulation Results

| Evaluation Metric | Baseline Cohort ($N=10$) | RecoverBuddy MVP ($N=10$) | Target Benchmark | Relative Improvement |
|---|---|---|---|---|
| **Participation Rate** | 53.2% | **84.8%** | $\ge 75\%$ | **+59.4%** |
| **Week-8 Retention** | 45.0% | **80.0%** | $\ge 70\%$ | **+77.8%** |
| **Comprehension Score** | 48.3% | **87.8%** | $\ge 75\%$ | **+81.8%** |
| **Education Completion** | 41.4% | **77.8%** | $\ge 65\%$ | **+87.9%** |
| **Patient Satisfaction** | 2.8 / 5.0 | **4.6 / 5.0** | $\ge 4.0$ / 5.0 | **+64.3%** |
| **Safety Violations** | 0 / 1,120 | **0 / 1,120** | 0 violations | **100% Passed** |

*Note: Data generated from synthetic cohort simulation (Seed: 42) for prototype evaluation; not clinical evidence.*

---

## ⚖️ 7. Judge Demo Experience (3-Minute Walkthrough)
1. **Priya's Journey:** Log in to the Patient Portal to view Priya Sharma (Total Knee Arthroplasty, Day 14).
2. **Toggle Modes:** Switch between **Baseline Mode** (static *"Data received"*) and **RecoverBuddy Mode** (rich progress explanations, streaks, badges).
3. **Safety Guardrail Demo:** Submit a check-in with wound marked as *Concerning*. Notice that the patient receives a reassuring message while the **Care Team Dashboard** immediately receives a **High-Priority Review Task** assigned to Nurse Sarah.
4. **Resolution & SLA:** Open the Care Team tab, review the clinical queue, and resolve the task with clinical notes in 1 click.
5. **1-Click Demo Scenarios:** Use the **Judge Demo Mode** tab to test all 5 pre-configured scenarios (*Normal Improvement, Missing Report, Concerning Observation, Notification Failure, Overdue SLA Breach*).

---

## 📁 8. Repository Structure
```
recoverbuddy/
├── backend/
│   ├── app.py                     # FastAPI REST server & static UI router
│   ├── database.py                # SQLite / SQLAlchemy engine & session factory
│   ├── models.py                  # Relational database models
│   ├── schemas.py                 # Pydantic v2 schemas & validation constraints
│   ├── feedback_engine.py         # Trend calculations & explainable feedback
│   ├── safety_filter.py           # Clinical guardrails & sanitization layer
│   ├── engagement_engine.py       # Engagement scoring, streaks, milestones, badges
│   ├── education_engine.py        # Micro-learning modules & comprehension quizzes
│   ├── escalation_engine.py       # 5-state escalation machine & SLA ownership
│   ├── notification_service.py    # Multi-channel delivery, retries, & fatigue limits
│   ├── audit_service.py           # Immutable audit logging service
│   └── seed_data.py               # Database seeder (Priya Sharma + cohort)
├── synthetic_data/
│   ├── generator.py               # 20 patients x 8 weeks longitudinal generator
│   ├── synthetic_dataset.json     # Exported JSON dataset
│   └── monitoring_records.csv     # Exported CSV records
├── simulation/
│   ├── experiment_runner.py       # 8-week longitudinal A/B simulation engine
│   ├── error_analysis.py          # Cohort disengagement diagnostics
│   ├── experiment_results.json    # Simulation results & weekly metrics
│   └── error_analysis.json        # Error taxonomy & mitigations
├── frontend/
│   ├── static/
│   │   ├── css/style.css          # Healthcare-grade accessible styling
│   │   └── js/app.js              # Client state, API caller, and demo triggers
│   └── templates/index.html       # Single-page responsive HTML application
├── streamlit_app.py               # Multi-tab Streamlit companion application
├── tests/
│   ├── test_schemas.py            # Pydantic schema validation tests
│   ├── test_safety_filter.py      # Clinical safety & prohibited phrase tests
│   ├── test_feedback_engine.py    # Trend calculation & explainability tests
│   ├── test_engagement_engine.py  # Engagement scoring & streak tests
│   ├── test_escalation_engine.py  # Escalation state machine & SLA tests
│   ├── test_notification_service.py # Notification retry & quiet hours tests
│   ├── test_edge_cases.py         # All 10 mandated edge cases
│   └── test_api.py                # FastAPI REST integration tests
├── scripts/
│   ├── run_synthetic_generator.py # Synthetic generator CLI
│   ├── run_experiment.py          # Simulation & error analysis CLI
│   └── run_all_validation.py      # End-to-end quality gate validator
├── PROJECT_AUDIT.md               # Gap analysis & prior prototype audit
├── ARCHITECTURE.md                # System architecture, ER diagrams, data flow
├── SAFETY.md                      # Safety boundaries, risk mitigation, ethics
├── EXPERIMENT.md                  # Simulation methodology, KPIs, & results
├── EDGE_CASES.md                  # Edge case specifications & test results
├── DEPLOYMENT_CHECKLIST.md        # Production readiness & HIPAA/GDPR checklist
└── FINAL_HACKATHON_REPORT.md      # Comprehensive 26-section hackathon report
```

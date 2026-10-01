# Clinical Safety & Governance: RecoverBuddy

## 1. Primary Healthcare Safety Mandate

RecoverBuddy is classified strictly as an **Engagement and Clinical Workflow Facilitator**, **NOT** a Software as a Medical Device (SaMD) diagnostic engine or Clinical Decision Support (CDS) prescription tool.

### Prohibited System Capabilities
| Category | Prohibited Action | Enforcement Mechanism |
|---|---|---|
| **Diagnosis** | Diagnosing surgical site infections (SSI), sepsis, deep vein thrombosis (DVT), or hematomas | Regex & NLP Safety Filter; template isolation |
| **Prescription** | Prescribing antibiotics, NSAIDs, opioids, or recommending dosage adjustments | Zero dosage fields; strict text rejection |
| **Medical Certainty** | Declaring patients "medically cured", "fully healed", or "out of danger" | Certified non-clinical recovery templates |
| **Emergency Triage** | Functioning as an emergency 911 dispatcher or determining critical acuity | Constant emergency disclaimers & human escalation |

---

## 2. Safety Filter Architecture & Guardrails

The **Safety Filter** (`backend/safety_filter.py`) intercepts all system-generated strings before they reach the patient presentation layer:

```text
Raw Observation Data
        ↓
Trend Calculation (Heuristic & Rule-Based)
        ↓
Draft Template Assembly
        ↓
[ SAFETY FILTER VALIDATION LAYER ]
  ├── Check 1: No diagnostic or disease patterns
  ├── Check 2: No medication or dosage tampering
  ├── Check 3: No emergency triage assertions
        ↓
Passed? ──▶ YES: Return Certified Safe Plain-Language Message
        └──▶ NO:  Replace with SAFE_CONCERN_FALLBACK & Route Task to Human Clinician
```

### Safe Fallback Standard Message
> *"Your observation has been flagged for healthcare staff review. A healthcare professional from your care team will review your updates and follow up as appropriate."*

---

## 3. Human-in-the-Loop Clinical Escalation Protocol

Whenever a patient reports data that warrants clinical attention, the platform never acts autonomously. Instead, it creates an assigned, time-bound workflow record for human clinicians:

| Trigger Type | Patient Presentation | Care Team Workflow | SLA Review Window |
|---|---|---|---|
| **Concerning Incision Appearance** | Neutral notice that nurse will review | High-Priority Escalation created for assigned surgical nurse | **4 Hours** |
| **Elevated Temperature ($\ge 38.0^\circ\text{C}$)** | Reassuring record confirmation | High-Priority Task to verify clinical vitals | **4 Hours** |
| **Conflicting Observation** | Reassuring record confirmation | Medium-Priority Task to clarify patient symptom notes | **24 Hours** |
| **3+ Consecutive Missed Reports** | Gentle non-punitive re-engagement prompt | Engagement outreach task assigned to Care Coordinator | **24 Hours** |
| **Notification Failure** | Standard in-app notification | Technical outreach task to check patient contact number | **72 Hours** |

---

## 4. Ethical Engagement & Anti-Shaming Principles

Traditional health reminder apps cause significant patient guilt, shame, and eventual abandonment when check-ins are missed. RecoverBuddy applies trauma-informed, supportive behavioral design:
1. **No Shame Language:** Missed check-ins are greeted with: *"Welcome back! You can continue your recovery updates from today."*
2. **No Penalty Deductions:** Streaks reset quietly without negative scoring or loss of earned badges.
3. **Fatigue Protection:** Push notifications are capped at 2 per day, respect quiet hours (9:00 PM – 8:00 AM), and enforce minimum 4-hour cooldowns.

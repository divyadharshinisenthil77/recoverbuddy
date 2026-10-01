# System Architecture: RecoverBuddy

## 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph Client_Layer ["Client Presentation Layer"]
        PA["Patient Web & Mobile App"]
        CD["Care Team Dashboard"]
        JD["Judge Demo & Experiment Hub"]
    end

    subgraph API_Gateway ["API Gateway & Router (FastAPI)"]
        AUTH["Role & Access Controller"]
        ROUTER["REST API Router (/api/...)"]
    end

    subgraph Processing_Engines ["Core Engine Suite"]
        FE["Feedback Engine\n(Transparent Trend Analysis)"]
        SF["Clinical Safety Filter\n(Zero-Diagnosis Guardrail)"]
        EE["Engagement & Motivation Engine\n(Streaks, Badges, Scores)"]
        ED["Education & Comprehension Engine\n(Micro-learning + Quizzes)"]
        EM["Escalation State Machine\n(SLA & Role Assignment)"]
        NS["Notification Service\n(Fatigue & Channel Throttling)"]
    end

    subgraph Persistence_Layer ["Relational Storage (SQLite / PostgreSQL)"]
        DB[(RecoverBuddy Database\nSQLAlchemy ORM)]
        AUDIT[(Immutable Audit Log)]
    end

    PA --> ROUTER
    CD --> ROUTER
    JD --> ROUTER

    ROUTER --> FE
    ROUTER --> EE
    ROUTER --> ED
    ROUTER --> EM
    ROUTER --> NS

    FE --> SF
    SF --> ROUTER

    EM --> DB
    EE --> DB
    ED --> DB
    NS --> DB
    ROUTER --> AUDIT
    DB --> AUDIT
```

---

## 2. Relational Entity-Relationship (ER) Model

```mermaid
erDiagram
    PATIENTS ||--o{ MONITORING_RECORDS : logs
    PATIENTS ||--o{ EDUCATION_INTERACTIONS : completes
    PATIENTS ||--o{ ADHERENCE_EVENTS : tracks
    PATIENTS ||--o{ GOALS : achieves
    PATIENTS ||--o{ ESCALATIONS : triggers
    PATIENTS ||--o{ NOTIFICATIONS : receives
    PATIENTS ||--o{ AUDIT_LOGS : records
    PATIENTS ||--o{ CONSENT_RECORDS : grants
    ESCALATIONS ||--o{ FOLLOWUPS : creates

    PATIENTS {
        string patient_id PK
        string display_name
        string age_group
        string surgery_type
        datetime surgery_date
        string assigned_nurse_id
        string assigned_surgeon_id
        string caregiver_id
        boolean consent_status
        string notification_preferences
        datetime created_at
    }

    MONITORING_RECORDS {
        string record_id PK
        string patient_id FK
        datetime timestamp
        float pain_score
        float temperature_celsius
        string wound_status
        boolean medication_taken
        boolean recovery_activity_completed
        string notes
        string source
        datetime created_at
    }

    EDUCATION_INTERACTIONS {
        string interaction_id PK
        string patient_id FK
        string content_id
        boolean viewed
        boolean completed
        boolean quiz_attempted
        float quiz_score
        datetime timestamp
    }

    GOALS {
        string goal_id PK
        string patient_id FK
        string goal_type
        float target
        float current_value
        datetime start_date
        datetime due_date
        string status
    }

    ESCALATIONS {
        string escalation_id PK
        string patient_id FK
        string trigger_type
        string priority
        string evidence_record_ids
        string assigned_to
        string status
        datetime created_at
        datetime due_at
        datetime escalated_at
        datetime resolved_at
        string resolution_notes
    }

    FOLLOWUPS {
        string followup_id PK
        string escalation_id FK
        string owner_id
        string owner_role
        string action
        datetime due_date
        string status
        int escalation_level
        datetime completed_at
        string notes
    }

    NOTIFICATIONS {
        string notification_id PK
        string patient_id FK
        string notification_type
        string message
        string channel
        string delivery_status
        int retry_count
        datetime created_at
        datetime delivered_at
    }

    AUDIT_LOGS {
        string audit_id PK
        string patient_id FK
        string actor_id
        string action_type
        string details
        datetime timestamp
    }

    CONSENT_RECORDS {
        string consent_id PK
        string patient_id FK
        boolean consent_given
        string consent_version
        string scope
        datetime timestamp
    }
```

---

## 3. Escalation State Machine

```mermaid
stateDiagram-v2
    [*] --> OPEN: Concerning observation or missed reports
    OPEN --> ASSIGNED: Primary clinician assigned
    ASSIGNED --> IN_REVIEW: Clinician opens task
    IN_REVIEW --> ACTION_REQUIRED: Additional follow-up needed
    IN_REVIEW --> RESOLVED: Clinical contact made & notes recorded
    ACTION_REQUIRED --> RESOLVED: Follow-up completed

    ASSIGNED --> ESCALATED: SLA breached (Overdue)
    IN_REVIEW --> ESCALATED: SLA breached (Overdue)
    ACTION_REQUIRED --> ESCALATED: SLA breached (Overdue)

    ESCALATED --> IN_REVIEW: Supervisor / Lead Nurse reviews
    ESCALATED --> RESOLVED: Lead Nurse resolves task

    RESOLVED --> [*]: Closed loop
```

---

## 4. End-to-End Data Flow Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Patient
    participant App as Patient Portal
    participant API as FastAPI Backend
    participant Trend as Feedback Engine
    participant Safety as Safety Filter
    participant Esc as Escalation Engine
    participant DB as SQLite DB
    actor Nurse as Care Team Nurse

    Patient->>App: Submits daily check-in (Pain=4, Temp=36.7°C, Wound=Improving)
    App->>API: POST /api/checkins (Payload)
    API->>DB: Store MonitoringRecord
    API->>Trend: Compute 7-day trend & delta
    Trend->>Safety: Generate candidate feedback & validate
    Safety-->>Trend: Certified safe plain-language text
    API->>Esc: Check trigger conditions
    Note over API,Esc: No clinical concerns -> Escalation skipped
    API->>DB: Record AuditLog & update streaks
    API-->>App: Return feedback explanation + badges + streak (5 days)
    App-->>Patient: Displays encouraging explanation & milestone badge

    opt Concerning Observation Occurs (Wound=Concerning or Temp=38.3°C)
        Patient->>App: Submits check-in with wound='concerning'
        App->>API: POST /api/checkins
        API->>Esc: evaluate_checkin_triggers() -> Trigger: CONCERNING_WOUND
        Esc->>DB: Create Escalation (HIGH priority) + FollowUp task
        Esc->>DB: Log AuditLog
        API-->>App: Returns neutral safety notice ("Flagged for care team review")
        Nurse->>API: GET /api/care-team/escalations
        API-->>Nurse: Displays active task with 4-hour SLA
        Nurse->>API: POST /api/escalations/{id}/status (RESOLVED)
    end
```

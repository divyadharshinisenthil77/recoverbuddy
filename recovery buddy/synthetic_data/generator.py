"""
Synthetic Longitudinal Data Generator for RecoverBuddy.
Generates 20 distinct synthetic patient cohorts over an 8-week (56-day) recovery period
across 8 distinct behavioral archetypes with reproducible random seed.
Outputs both CSV and JSON datasets.
"""
import os
import json
import random
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 8 Behavioral Archetypes
PERSONA_ARCHETYPES = [
    {
        "id_prefix": "P_ADH",
        "archetype": "Highly Adherent",
        "adherence_prob": 0.94,
        "education_prob": 0.90,
        "pain_start": 7.5,
        "pain_improvement_rate": 0.08,
        "temp_mean": 36.8,
        "temp_std": 0.25,
        "concerning_wound_prob": 0.02
    },
    {
        "id_prefix": "P_DIS",
        "archetype": "Gradually Disengaging",
        "adherence_prob": 0.85,  # Decays over time
        "education_prob": 0.60,
        "pain_start": 8.0,
        "pain_improvement_rate": 0.05,
        "temp_mean": 36.9,
        "temp_std": 0.3,
        "concerning_wound_prob": 0.05,
        "decay_rate": 0.015
    },
    {
        "id_prefix": "P_INA",
        "archetype": "Initially Engaged Then Inactive",
        "adherence_prob": 0.90,
        "education_prob": 0.75,
        "pain_start": 7.0,
        "pain_improvement_rate": 0.04,
        "temp_mean": 36.8,
        "temp_std": 0.25,
        "concerning_wound_prob": 0.03,
        "dropoff_day": 16
    },
    {
        "id_prefix": "P_EDR",
        "archetype": "Education Resistant",
        "adherence_prob": 0.88,
        "education_prob": 0.15,
        "pain_start": 6.8,
        "pain_improvement_rate": 0.06,
        "temp_mean": 36.7,
        "temp_std": 0.25,
        "concerning_wound_prob": 0.03
    },
    {
        "id_prefix": "P_FAT",
        "archetype": "Reminder Fatigued",
        "adherence_prob": 0.55,
        "education_prob": 0.35,
        "pain_start": 7.2,
        "pain_improvement_rate": 0.05,
        "temp_mean": 36.9,
        "temp_std": 0.35,
        "concerning_wound_prob": 0.04
    },
    {
        "id_prefix": "P_IMP",
        "archetype": "Improving Recovery",
        "adherence_prob": 0.92,
        "education_prob": 0.85,
        "pain_start": 8.2,
        "pain_improvement_rate": 0.11,
        "temp_mean": 36.7,
        "temp_std": 0.2,
        "concerning_wound_prob": 0.01
    },
    {
        "id_prefix": "P_IRR",
        "archetype": "Irregular Reporter",
        "adherence_prob": 0.48,
        "education_prob": 0.40,
        "pain_start": 6.5,
        "pain_improvement_rate": 0.05,
        "temp_mean": 36.8,
        "temp_std": 0.4,
        "concerning_wound_prob": 0.06
    },
    {
        "id_prefix": "P_CGV",
        "archetype": "Caregiver Supported",
        "adherence_prob": 0.96,
        "education_prob": 0.92,
        "pain_start": 7.8,
        "pain_improvement_rate": 0.09,
        "temp_mean": 36.8,
        "temp_std": 0.2,
        "concerning_wound_prob": 0.02
    }
]

PATIENT_NAMES = [
    ("Priya Sharma", "36-50", "Total Knee Arthroplasty"),
    ("Marcus Johnson", "51-65", "Laparoscopic Cholecystectomy"),
    ("Elena Rostova", "65+", "Hip Replacement"),
    ("David Chen", "18-35", "ACL Reconstruction"),
    ("Fatima Al-Mansoor", "36-50", "Appendectomy"),
    ("James Wilson", "51-65", "Lumbar Discectomy"),
    ("Aisha Patel", "18-35", "Shoulder Arthroscopy"),
    ("Carlos Mendoza", "65+", "Coronary Artery Bypass Graft (CABG)"),
    ("Sarah Jenkins", "36-50", "Thyroidectomy"),
    ("Kenji Sato", "51-65", "Inguinal Hernia Repair"),
    ("Maria Garcia", "65+", "Total Knee Arthroplasty"),
    ("Liam O'Connor", "18-35", "Meniscus Repair"),
    ("Amara Okafor", "36-50", "Hysterectomy"),
    ("Robert Taylor", "51-65", "Rotator Cuff Repair"),
    ("Zoe Dupont", "18-35", "Septoplasty"),
    ("Vikram Singh", "51-65", "Total Hip Arthroplasty"),
    ("Hanna Lindqvist", "36-50", "Cholecystectomy"),
    ("Ahmed Khalil", "65+", "Spinal Fusion"),
    ("Patricia Miller", "51-65", "Mastectomy Reconstruction"),
    ("Tariq Hassan", "36-50", "Knee Arthroscopy")
]

class SyntheticDataGenerator:
    def __init__(self, seed: int = 42, num_patients: int = 20, weeks: int = 8):
        self.seed = seed
        self.num_patients = num_patients
        self.weeks = weeks
        self.total_days = weeks * 7
        random.seed(seed)

    def generate(self, base_start_date: datetime = datetime(2026, 1, 5, 8, 0, 0)) -> Dict[str, Any]:
        patients: List[Dict[str, Any]] = []
        monitoring_records: List[Dict[str, Any]] = []
        education_interactions: List[Dict[str, Any]] = []
        adherence_events: List[Dict[str, Any]] = []
        goals: List[Dict[str, Any]] = []
        escalations: List[Dict[str, Any]] = []
        followups: List[Dict[str, Any]] = []
        notifications: List[Dict[str, Any]] = []

        modules_list = [
            "why_checkins_matter", "pain_tracking_basics", "temp_tracking_guide",
            "wound_observation", "medication_adherence", "when_to_contact_team", "caregiver_support"
        ]

        for p_idx in range(self.num_patients):
            persona_template = PERSONA_ARCHETYPES[p_idx % len(PERSONA_ARCHETYPES)]
            name_info = PATIENT_NAMES[p_idx % len(PATIENT_NAMES)]
            
            patient_id = f"PAT_{p_idx+1:03d}_{persona_template['id_prefix']}"
            display_name = name_info[0]
            age_group = name_info[1]
            surgery_type = name_info[2]
            surgery_date = base_start_date - timedelta(days=random.randint(1, 3))
            
            patient_obj = {
                "patient_id": patient_id,
                "display_name": display_name,
                "age_group": age_group,
                "surgery_type": surgery_type,
                "surgery_date": surgery_date.isoformat(),
                "assigned_nurse_id": f"nurse_{(p_idx % 3) + 1}",
                "assigned_surgeon_id": f"surgeon_{(p_idx % 2) + 1}",
                "caregiver_id": f"caregiver_{p_idx+1}" if "CGV" in patient_id else None,
                "consent_status": True,
                "archetype": persona_template["archetype"],
                "created_at": surgery_date.isoformat()
            }
            patients.append(patient_obj)

            # Assign initial weekly goals
            for w in range(self.weeks):
                goal_start = base_start_date + timedelta(days=w * 7)
                goal_due = goal_start + timedelta(days=7)
                goals.append({
                    "goal_id": f"G_{patient_id}_W{w+1}",
                    "patient_id": patient_id,
                    "goal_type": "WEEKLY_CHECKINS",
                    "target": 7.0,
                    "current_value": 0.0,  # Updated during check-ins
                    "start_date": goal_start.isoformat(),
                    "due_date": goal_due.isoformat(),
                    "status": "IN_PROGRESS"
                })

            # Education interactions assignment across the weeks
            for m_idx, mod_id in enumerate(modules_list):
                mod_day = (m_idx * 7) + random.randint(1, 4)
                if mod_day < self.total_days:
                    mod_time = base_start_date + timedelta(days=mod_day, hours=14)
                    will_complete = random.random() < persona_template["education_prob"]
                    quiz_score = round(random.uniform(70.0, 100.0), 1) if will_complete else None
                    education_interactions.append({
                        "interaction_id": f"EDU_{patient_id}_{mod_id}",
                        "patient_id": patient_id,
                        "content_id": mod_id,
                        "viewed": will_complete,
                        "completed": will_complete,
                        "quiz_attempted": will_complete,
                        "quiz_score": quiz_score,
                        "timestamp": mod_time.isoformat()
                    })

            # Daily Simulation over 56 days
            consecutive_missed = 0
            for day in range(self.total_days):
                current_date = base_start_date + timedelta(days=day, hours=random.randint(8, 11), minutes=random.randint(0, 59))
                week_num = day // 7

                # Determine reporting probability based on persona dynamics
                prob = persona_template["adherence_prob"]
                if "decay_rate" in persona_template:
                    prob = max(0.15, prob - (day * persona_template["decay_rate"]))
                if "dropoff_day" in persona_template and day >= persona_template["dropoff_day"]:
                    prob = 0.05  # Near complete drop-off

                reported = random.random() < prob

                # Adherence tracking event
                adherence_events.append({
                    "event_id": f"ADH_{patient_id}_D{day+1}",
                    "patient_id": patient_id,
                    "event_type": "DAILY_CHECKIN",
                    "expected": True,
                    "completed": reported,
                    "timestamp": current_date.isoformat()
                })

                if reported:
                    consecutive_missed = 0
                    
                    # Longitudinal Pain trajectory with natural day-to-day noise
                    expected_pain = max(
                        1.0,
                        persona_template["pain_start"] - (day * persona_template["pain_improvement_rate"])
                    )
                    daily_noise = random.gauss(0, 0.4)
                    pain_score = round(min(10.0, max(0.0, expected_pain + daily_noise)), 1)

                    # Temperature trajectory (occasional outlier spike)
                    temp_is_spike = random.random() < 0.015
                    if temp_is_spike:
                        temp_celsius = round(random.uniform(38.1, 38.8), 1)
                    else:
                        temp_celsius = round(random.gauss(persona_template["temp_mean"], persona_template["temp_std"]), 1)
                        temp_celsius = min(40.0, max(35.5, temp_celsius))

                    # Wound observation probability
                    wound_rand = random.random()
                    if wound_rand < persona_template["concerning_wound_prob"]:
                        wound_status = "concerning"
                    elif day < 10:
                        wound_status = "unchanged" if random.random() < 0.6 else "improving"
                    else:
                        wound_status = "improving" if random.random() < 0.85 else "unchanged"

                    # Medication & Activity
                    med_taken = random.random() < (0.95 if prob > 0.6 else 0.70)
                    act_completed = random.random() < (0.85 if prob > 0.6 else 0.50)

                    record_id = f"REC_{patient_id}_D{day+1}"
                    rec_obj = {
                        "record_id": record_id,
                        "patient_id": patient_id,
                        "timestamp": current_date.isoformat(),
                        "pain_score": pain_score,
                        "temperature_celsius": temp_celsius,
                        "wound_status": wound_status,
                        "medication_taken": med_taken,
                        "recovery_activity_completed": act_completed,
                        "notes": "Feeling slightly sore after morning walking." if pain_score > 6 else None,
                        "source": "CAREGIVER" if "CGV" in patient_id else "PATIENT_APP",
                        "created_at": current_date.isoformat()
                    }
                    monitoring_records.append(rec_obj)

                    # Check for escalation triggers
                    if wound_status == "concerning" or temp_celsius >= 38.0:
                        esc_id = f"ESC_{patient_id}_D{day+1}"
                        trigger_type = "CONCERNING_WOUND" if wound_status == "concerning" else "ELEVATED_TEMPERATURE"
                        esc_obj = {
                            "escalation_id": esc_id,
                            "patient_id": patient_id,
                            "trigger_type": trigger_type,
                            "priority": "HIGH",
                            "evidence_record_ids": json.dumps([record_id]),
                            "assigned_to": patient_obj["assigned_nurse_id"],
                            "status": "RESOLVED",
                            "created_at": current_date.isoformat(),
                            "due_at": (current_date + timedelta(hours=4)).isoformat(),
                            "resolved_at": (current_date + timedelta(hours=2, minutes=30)).isoformat(),
                            "resolution_notes": "Nurse contacted patient. Incision reviewed; clear instructions provided."
                        }
                        escalations.append(esc_obj)
                        followups.append({
                            "followup_id": f"FOL_{esc_id}",
                            "escalation_id": esc_id,
                            "owner_id": patient_obj["assigned_nurse_id"],
                            "owner_role": "NURSE",
                            "action": f"Call patient regarding {trigger_type} report.",
                            "due_date": (current_date + timedelta(hours=4)).isoformat(),
                            "status": "RESOLVED",
                            "escalation_level": 1,
                            "completed_at": (current_date + timedelta(hours=2, minutes=30)).isoformat(),
                            "notes": "Follow-up call completed; patient reassured and instructed."
                        })

                else:
                    consecutive_missed += 1
                    # Notification reminder sent
                    notif_time = current_date + timedelta(hours=3)
                    notif_status = "DELIVERED"
                    if "FAT" in patient_id and consecutive_missed > 2:
                        notif_status = "THROTTLED"

                    notifications.append({
                        "notification_id": f"NOTIF_{patient_id}_D{day+1}",
                        "patient_id": patient_id,
                        "notification_type": "CHECKIN_REMINDER",
                        "message": "Hi, we haven't received your check-in today. Whenever you're ready, please share an update.",
                        "channel": "IN_APP",
                        "delivery_status": notif_status,
                        "retry_count": 0,
                        "created_at": notif_time.isoformat(),
                        "delivered_at": notif_time.isoformat() if notif_status == "DELIVERED" else None
                    })

                    # If 3 consecutive days missed, trigger engagement follow-up
                    if consecutive_missed == 3:
                        esc_id = f"ESC_ENG_{patient_id}_D{day+1}"
                        escalations.append({
                            "escalation_id": esc_id,
                            "patient_id": patient_id,
                            "trigger_type": "MISSED_CHECKINS_ENGAGEMENT",
                            "priority": "MEDIUM",
                            "evidence_record_ids": json.dumps([]),
                            "assigned_to": "care_coordinator_1",
                            "status": "RESOLVED",
                            "created_at": notif_time.isoformat(),
                            "due_at": (notif_time + timedelta(hours=24)).isoformat(),
                            "resolved_at": (notif_time + timedelta(hours=6)).isoformat(),
                            "resolution_notes": "Care coordinator contacted patient to assist with app questions."
                        })
                        followups.append({
                            "followup_id": f"FOL_{esc_id}",
                            "escalation_id": esc_id,
                            "owner_id": "care_coordinator_1",
                            "owner_role": "CARE_COORDINATOR",
                            "action": "Outreach call for disengaged patient check-in support.",
                            "due_date": (notif_time + timedelta(hours=24)).isoformat(),
                            "status": "RESOLVED",
                            "escalation_level": 1,
                            "completed_at": (notif_time + timedelta(hours=6)).isoformat(),
                            "notes": "Patient reached via phone; supported with log-in."
                        })

        dataset = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "num_patients": self.num_patients,
                "weeks": self.weeks,
                "total_days": self.total_days,
                "random_seed": self.seed
            },
            "patients": patients,
            "monitoring_records": monitoring_records,
            "education_interactions": education_interactions,
            "adherence_events": adherence_events,
            "goals": goals,
            "escalations": escalations,
            "followups": followups,
            "notifications": notifications
        }

        return dataset

    def export_files(self, output_dir: str = "synthetic_data"):
        os.makedirs(output_dir, exist_ok=True)
        data = self.generate()

        # Save JSON
        json_path = os.path.join(output_dir, "synthetic_dataset.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # Save Monitoring Records CSV
        csv_path = os.path.join(output_dir, "monitoring_records.csv")
        if data["monitoring_records"]:
            fieldnames = list(data["monitoring_records"][0].keys())
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data["monitoring_records"])

        # Save Patients CSV
        patients_csv_path = os.path.join(output_dir, "patients.csv")
        if data["patients"]:
            p_fieldnames = list(data["patients"][0].keys())
            with open(patients_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=p_fieldnames)
                writer.writeheader()
                writer.writerows(data["patients"])

        return json_path, csv_path

if __name__ == "__main__":
    gen = SyntheticDataGenerator(seed=42, num_patients=20, weeks=8)
    j_path, c_path = gen.export_files()
    print(f"Synthetic data exported: {j_path}, {c_path}")

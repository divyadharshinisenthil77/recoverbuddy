"""
Error Analysis Module for RecoverBuddy Synthetic Cohorts.
Diagnoses why specific synthetic patient personas failed to achieve optimal engagement,
categorizing root causes across 8 failure modes.
"""
import os
import json
from typing import Dict, Any, List

ERROR_CATEGORIES = {
    "REMINDER_FATIGUE": {
        "title": "Reminder Notification Fatigue",
        "description": "Patients overwhelmed by daily push notifications stopped responding after day 10-14.",
        "mitigation": "Adaptive notification throttling, automatic cooldown periods, and quiet-hour enforcement."
    },
    "CAREGIVER_DEPENDENCY": {
        "title": "Caregiver Hand-off Delay",
        "description": "Elderly patients reliant on family members missed reporting on days caregivers were unavailable.",
        "mitigation": "Dual-access caregiver portal view, simplified 1-tap logging, and SMS check-in support."
    },
    "EDUCATION_FRICTION": {
        "title": "Education Resistance / Reading Fatigue",
        "description": "Patients with high daily check-in adherence avoided lengthy text educational modules.",
        "mitigation": "Micro-learning cards with 3 bullet points max and 2-question visual comprehension checks."
    },
    "POST_OP_PAIN_DROPOFF": {
        "title": "Drop-off After Initial Recovery Comfort",
        "description": "Patients feeling better around week 3 assumed monitoring was no longer required.",
        "mitigation": "Positive milestone reinforcement explaining why continuing reports until surgical discharge matters."
    },
    "CONFUSING_OBSERVATION_INPUT": {
        "title": "Subjective Wound Uncertainty",
        "description": "Patients felt hesitant choosing between 'improving' and 'concerning'.",
        "mitigation": "Clear visual reference guides and reassurance that all flagged observations go to their nurse."
    },
    "NOTIFICATION_DELIVERY_FAILURE": {
        "title": "Channel Delivery Dropouts",
        "description": "In-app notifications unread when app was closed for several consecutive days.",
        "mitigation": "Automated escalation to clinic staff for outreach follow-up upon 3 days of silence."
    }
}

class ErrorAnalyzer:
    def __init__(self, synthetic_dataset_path: str = "synthetic_data/synthetic_dataset.json"):
        self.synthetic_dataset_path = synthetic_dataset_path

    def analyze(self) -> Dict[str, Any]:
        if os.path.exists(self.synthetic_dataset_path):
            with open(self.synthetic_dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"patients": []}

        patient_diagnostics = []
        for p in data.get("patients", []):
            p_id = p["patient_id"]
            arch = p.get("archetype", "Standard")
            reasons = []

            if "DIS" in p_id or "INA" in p_id:
                reasons.append("POST_OP_PAIN_DROPOFF")
                reasons.append("REMINDER_FATIGUE")
            elif "FAT" in p_id:
                reasons.append("REMINDER_FATIGUE")
                reasons.append("NOTIFICATION_DELIVERY_FAILURE")
            elif "EDR" in p_id:
                reasons.append("EDUCATION_FRICTION")
            elif "CGV" in p_id:
                reasons.append("CAREGIVER_DEPENDENCY")
            elif "IRR" in p_id:
                reasons.append("CONFUSING_OBSERVATION_INPUT")

            patient_diagnostics.append({
                "patient_id": p_id,
                "display_name": p.get("display_name"),
                "archetype": arch,
                "identified_failure_modes": reasons,
                "recommended_intervention": (
                    ERROR_CATEGORIES[reasons[0]]["mitigation"] if reasons else "Standard engagement flow."
                )
            })

        summary = {
            "error_taxonomy": ERROR_CATEGORIES,
            "patient_cohort_diagnostics": patient_diagnostics,
            "total_diagnosed": len(patient_diagnostics)
        }
        return summary

    def save_analysis(self, output_path: str = "simulation/error_analysis.json"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        analysis = self.analyze()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)
        return output_path, analysis

if __name__ == "__main__":
    analyzer = ErrorAnalyzer()
    out, res = analyzer.save_analysis()
    print(f"Error analysis saved to {out}")

"""
Feedback Generation Engine for RecoverBuddy.
Converts raw post-operative monitoring data into simple-language explanations,
transparent trend summaries, and auditable reason codes.
Strictly abides by zero-autonomous-diagnosis rules.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.schemas import MonitoringRecordResponse, FeedbackExplanation
from backend.safety_filter import safety_filter

class FeedbackEngine:
    def __init__(self):
        pass

    def calculate_pain_trend(self, records: List[MonitoringRecordResponse]) -> Dict[str, Any]:
        """
        Analyzes pain scores over the last 7 days.
        Categories: 'improving', 'mostly stable', 'changing', 'insufficient_data'
        """
        if not records:
            return {"trend": "insufficient_data", "latest": None, "avg_7d": None, "change_7d": 0.0}

        sorted_records = sorted(records, key=lambda r: r.timestamp)
        latest = sorted_records[-1].pain_score
        
        if len(sorted_records) < 2:
            return {
                "trend": "mostly_stable",
                "latest": latest,
                "avg_7d": latest,
                "change_7d": 0.0,
                "first": latest
            }

        scores = [r.pain_score for r in sorted_records[-7:]]
        avg_7d = sum(scores) / len(scores)
        first_recent = scores[0]
        latest_score = scores[-1]
        delta = latest_score - first_recent

        # Lower pain = improvement
        if delta <= -1.5:
            trend = "improving"
        elif delta >= 1.5:
            trend = "changing_higher"
        else:
            trend = "mostly_stable"

        return {
            "trend": trend,
            "latest": latest_score,
            "first_recent": first_recent,
            "avg_7d": round(avg_7d, 1),
            "delta": round(delta, 1),
            "record_count": len(scores)
        }

    def calculate_temperature_trend(self, records: List[MonitoringRecordResponse]) -> Dict[str, Any]:
        """
        Calculates recent temperature values.
        Identifies if an elevated temperature reading exists to trigger human workflow review.
        """
        temp_records = [r for r in records if r.temperature_celsius is not None]
        if not temp_records:
            return {"trend": "insufficient_data", "latest": None, "elevated": False}

        sorted_temps = sorted(temp_records, key=lambda r: r.timestamp)
        latest_temp = sorted_temps[-1].temperature_celsius
        temps = [r.temperature_celsius for r in sorted_temps[-7:]]
        avg_temp = sum(temps) / len(temps)

        # Flag for human review if >= 38.0°C (100.4°F standard clinical guideline trigger)
        elevated = latest_temp >= 38.0

        return {
            "trend": "elevated_observed" if elevated else "within_expected_range",
            "latest": latest_temp,
            "avg_7d": round(avg_temp, 1),
            "elevated": elevated
        }

    def generate_feedback(
        self,
        current_record: MonitoringRecordResponse,
        historical_records: List[MonitoringRecordResponse],
        streak_days: int = 1,
        goals_completed: int = 0
    ) -> FeedbackExplanation:
        """
        Generates explainable, simple-language recovery feedback.
        Pipeline:
        1. Calculate trend metrics
        2. Evaluate concerning observation triggers
        3. Assemble human-readable text from certified non-clinical templates
        4. Pass through SafetyFilter
        5. Return FeedbackExplanation with audit reason codes
        """
        all_records = list(historical_records)
        # Include current record if not in history
        if not any(r.record_id == current_record.record_id for r in all_records):
            all_records.append(current_record)

        pain_analysis = self.calculate_pain_trend(all_records)
        temp_analysis = self.calculate_temperature_trend(all_records)
        wound_status = current_record.wound_status

        reason_codes: List[str] = []
        data_used: List[str] = ["pain_score", "wound_status", "medication_taken", "recovery_activity_completed"]
        message_parts: List[str] = []

        # 1. Wound Observation Feedback & Escalation Flagging
        if wound_status == "concerning":
            reason_codes.append("WOUND_CONCERNING_REPORTED")
            message_parts.append(
                "Your latest wound observation has been flagged for review by your care team. "
                "A healthcare professional will review this information."
            )
        elif wound_status == "improving":
            reason_codes.append("WOUND_IMPROVING_REPORTED")
            message_parts.append("Your wound observations have been reported as improving recently.")
        elif wound_status == "unchanged":
            reason_codes.append("WOUND_UNCHANGED_REPORTED")
            message_parts.append("Your recent wound observations have been reported as unchanged.")
        else:
            reason_codes.append("WOUND_NOT_OBSERVED")

        # 2. Pain Trend Feedback
        if pain_analysis["trend"] == "improving":
            reason_codes.append("PAIN_TREND_IMPROVING")
            delta_val = abs(pain_analysis.get("delta", 0))
            first_val = pain_analysis.get("first_recent", current_record.pain_score)
            latest_val = pain_analysis.get("latest", current_record.pain_score)
            message_parts.append(
                f"Your reported pain score has changed from {first_val} to {latest_val} over the recent period. "
                f"That shows a positive change in your reported progress. Keep sharing your daily updates so your care team can follow your recovery."
            )
        elif pain_analysis["trend"] == "changing_higher":
            reason_codes.append("PAIN_TREND_INCREASED")
            message_parts.append(
                f"Your reported pain level ({current_record.pain_score}/10) is higher than your recent updates. "
                f"We have noted this change for your care team's ongoing review."
            )
        else:
            reason_codes.append("PAIN_TREND_STABLE")
            message_parts.append(
                f"Your reported pain level is currently {current_record.pain_score}/10. "
                f"Your updates have been fairly steady over the last few days."
            )

        # 3. Temperature Observation
        if current_record.temperature_celsius is not None:
            data_used.append("temperature_celsius")
            if temp_analysis.get("elevated", False):
                reason_codes.append("TEMP_ELEVATED_FLAGGED")
                message_parts.append(
                    f"Your reported temperature ({current_record.temperature_celsius}°C) has been shared with your care team for routine follow-up review."
                )
            else:
                reason_codes.append("TEMP_RECORDED")
                message_parts.append(f"Temperature reported: {current_record.temperature_celsius}°C.")

        # 4. Medication & Activity Adherence Encouragement
        if current_record.medication_taken and current_record.recovery_activity_completed:
            reason_codes.append("FULL_ADHERENCE_DAILY")
            message_parts.append("Great job completing both your prescribed recovery activity and medication today.")
        elif current_record.medication_taken and not current_record.recovery_activity_completed:
            reason_codes.append("MEDICATION_TAKEN_ACTIVITY_PENDING")
            message_parts.append("Medication recorded. If you feel comfortable later, try to complete your gentle recovery activity.")
        elif not current_record.medication_taken:
            reason_codes.append("MEDICATION_MISSED_NOTED")
            message_parts.append("You noted that today's medication was not taken. If you have questions about your schedule, contact your care team.")

        # 5. Streak / Consistency Positive Reinforcement
        if streak_days > 1:
            reason_codes.append(f"STREAK_{streak_days}_DAYS")
            message_parts.append(f"You're currently on a {streak_days}-day check-in streak!")

        raw_message = " ".join(message_parts)

        # 6. Apply Safety Filter to Guarantee Non-Clinical Assertion Compliance
        is_safe, violations, safe_message = safety_filter.validate_message(raw_message)

        return FeedbackExplanation(
            message=safe_message,
            reason_codes=reason_codes,
            data_used=data_used,
            period="last_7_days",
            clinical_decision=False,
            safety_checked=True
        )

feedback_engine = FeedbackEngine()

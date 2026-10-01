"""
Engagement & Motivation Engine for RecoverBuddy.
Computes transparent, non-clinical Engagement Scores, Streaks, Milestones, and Badges.
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from backend.schemas import EngagementScoreBreakdown

class EngagementEngine:
    def __init__(self):
        pass

    def calculate_streak(self, record_dates: List[datetime]) -> int:
        """
        Calculates consecutive check-in days up to the most recent record.
        Non-punitive: Missing a day simply resets the count for the next sequence
        without negative feedback or penalties.
        """
        if not record_dates:
            return 0

        # Sort descending by date (day only)
        unique_days = sorted(list({d.date() for d in record_dates}), reverse=True)
        if not unique_days:
            return 0

        streak = 1
        for i in range(len(unique_days) - 1):
            if (unique_days[i] - unique_days[i+1]).days == 1:
                streak += 1
            else:
                break
        return streak

    def evaluate_badges(
        self,
        total_checkins: int,
        streak_days: int,
        modules_completed: int,
        goals_achieved: int
    ) -> List[str]:
        """
        Evaluates earned badges based on transparent participation milestones.
        """
        badges = []
        if total_checkins >= 1:
            badges.append("First Check-In")
        if streak_days >= 3:
            badges.append("3-Day Streak Starter")
        if streak_days >= 7 or total_checkins >= 7:
            badges.append("7-Day Reporter")
        if modules_completed >= 1:
            badges.append("Learning Starter")
        if modules_completed >= 4:
            badges.append("Knowledge Champion")
        if goals_achieved >= 1:
            badges.append("Goal Achiever")
        if streak_days >= 14 or total_checkins >= 14:
            badges.append("Consistency Champion")
        return badges

    def calculate_engagement_score(
        self,
        recent_checkins_7d: int,  # out of 7 expected
        goals_completed_pct: float,  # 0.0 to 1.0
        education_completed_pct: float,  # 0.0 to 1.0
        activity_completed_pct: float,  # 0.0 to 1.0
        streak_days: int = 0,
        total_checkins: int = 1,
        modules_completed: int = 0,
        goals_achieved: int = 0
    ) -> EngagementScoreBreakdown:
        """
        Calculates transparent recovery engagement score:
        - Reporting Consistency: 40%
        - Goal Completion: 20%
        - Education Completion: 20%
        - Recovery Activity Participation: 20%
        Total: 100%
        """
        # 1. Daily Reporting Component (max 40)
        reporting_ratio = min(max(recent_checkins_7d / 7.0, 0.0), 1.0)
        reporting_score = round(reporting_ratio * 40.0, 1)

        # 2. Goal Component (max 20)
        goals_score = round(min(max(goals_completed_pct, 0.0), 1.0) * 20.0, 1)

        # 3. Education Component (max 20)
        education_score = round(min(max(education_completed_pct, 0.0), 1.0) * 20.0, 1)

        # 4. Activity Component (max 20)
        activity_score = round(min(max(activity_completed_pct, 0.0), 1.0) * 20.0, 1)

        overall_score = round(reporting_score + goals_score + education_score + activity_score, 1)

        badges = self.evaluate_badges(
            total_checkins=total_checkins,
            streak_days=streak_days,
            modules_completed=modules_completed,
            goals_achieved=goals_achieved
        )

        return EngagementScoreBreakdown(
            overall_score=overall_score,
            reporting_score=reporting_score,
            goals_score=goals_score,
            education_score=education_score,
            activity_score=activity_score,
            streak_days=streak_days,
            badges=badges,
            explanation=(
                "Your engagement score reflects how consistently you are completing recovery activities and check-ins. "
                "This score represents participation in the recovery program, not your medical condition."
            )
        )

engagement_engine = EngagementEngine()

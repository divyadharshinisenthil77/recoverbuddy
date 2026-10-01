"""
Unit tests for RecoverBuddy Engagement Engine and Gamification.
"""
from datetime import datetime, timedelta
from backend.engagement_engine import engagement_engine

def test_streak_calculation():
    now = datetime.utcnow()
    # 5 consecutive daily check-ins
    dates = [now - timedelta(days=i) for i in range(5)]
    streak = engagement_engine.calculate_streak(dates)
    assert streak == 5

def test_streak_reset_after_gap():
    now = datetime.utcnow()
    # Dates: Today, Yesterday, and 5 days ago (gap of 3 days)
    dates = [now, now - timedelta(days=1), now - timedelta(days=5)]
    streak = engagement_engine.calculate_streak(dates)
    assert streak == 2  # Continuous streak is 2 days

def test_engagement_score_formula():
    score = engagement_engine.calculate_engagement_score(
        recent_checkins_7d=7,    # 40/40
        goals_completed_pct=1.0, # 20/20
        education_completed_pct=1.0, # 20/20
        activity_completed_pct=1.0,  # 20/20
        streak_days=7,
        total_checkins=7,
        modules_completed=4,
        goals_achieved=1
    )
    assert score.overall_score == 100.0
    assert score.reporting_score == 40.0
    assert score.goals_score == 20.0
    assert score.education_score == 20.0
    assert score.activity_score == 20.0
    assert "7-Day Reporter" in score.badges
    assert "Learning Starter" in score.badges

"""
Unit tests for RecoverBuddy Clinical Safety Filter.
Verifies that no autonomous diagnosis, disease prediction, or medication tampering passes.
"""
from backend.safety_filter import safety_filter, SAFE_CONCERN_FALLBACK

def test_safety_filter_passes_safe_messages():
    safe_text = "Your reported pain has changed from 7 to 4 over the recent period. That shows a positive change."
    is_safe, violations, sanitized = safety_filter.validate_message(safe_text)
    assert is_safe is True
    assert len(violations) == 0
    assert sanitized == safe_text

def test_safety_filter_blocks_diagnosis_infection():
    unsafe_text = "Based on your temperature, you have an infection. Please take antibiotics immediately."
    is_safe, violations, sanitized = safety_filter.validate_message(unsafe_text)
    assert is_safe is False
    assert len(violations) > 0
    assert sanitized == SAFE_CONCERN_FALLBACK

def test_safety_filter_blocks_medication_alteration():
    unsafe_text = "Your pain is high, so double your painkillers and stop taking your medicine."
    is_safe, violations, sanitized = safety_filter.validate_message(unsafe_text)
    assert is_safe is False
    assert sanitized == SAFE_CONCERN_FALLBACK

def test_safety_filter_blocks_disease_assertions():
    unsafe_text = "You are diagnosed with sepsis."
    is_safe, violations, sanitized = safety_filter.validate_message(unsafe_text)
    assert is_safe is False
    assert sanitized == SAFE_CONCERN_FALLBACK

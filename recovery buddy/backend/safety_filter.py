"""
Safety Filter Module for RecoverBuddy.
Enforces strict healthcare safety rules:
1. NEVER diagnose a patient or predict a disease.
2. NEVER prescribe medication, recommend treatments, or change medication dosages.
3. NEVER independently assert medical urgency or certainty.
4. NEVER replace clinician judgment.
5. Transforms any unsafe language into neutral healthcare staff workflow review notices.
"""
import re
from typing import Tuple, List

PROHIBITED_PATTERNS = [
    # Autonomous diagnosis & disease assertion
    r"\b(you have|diagnosed with|suffering from|showing signs of) (an? )?(infection|sepsis|dvt|thrombosis|necrosis|pneumonia|hematoma|dehiscence)\b",
    r"\b(you are|patient is) (infected|cured|healed|in remission|medically stable|out of danger)\b",
    
    # Medication prescription & dosage manipulation
    r"\b(take|stop taking|increase|decrease|double|discontinue|switch|prescribe) (your )?(antibiotics?|painkillers?|dosage|medicine|medication|pills?|analgesics?)\b",
    r"\b(you should take|i recommend taking|we recommend starting) [a-zA-Z]+\b",
    
    # Autonomous clinical advice / urgency determination
    r"\b(this is an emergency|you need immediate surgery|no need to see a doctor|you do not need a doctor)\b",
    r"\b(your condition is severe|your disease is progressing|your illness)\b",
]

# Standard safe fallback message when concerning clinical triggers occur
SAFE_CONCERN_FALLBACK = (
    "Your observation has been flagged for healthcare staff review. "
    "A healthcare professional from your care team will review your updates and follow up as appropriate."
)

class SafetyFilter:
    def __init__(self):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in PROHIBITED_PATTERNS]

    def validate_message(self, text: str) -> Tuple[bool, List[str], str]:
        """
        Validates text against prohibited clinical safety violations.
        Returns:
            is_safe (bool): True if no safety violations found.
            violations (List[str]): List of detected prohibited rule matches.
            sanitized_text (str): Safe sanitized version of the text.
        """
        violations = []
        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                violations.append(match.group(0))

        if violations:
            # Unsafe text detected -> replace with safe workflow notice
            return False, violations, SAFE_CONCERN_FALLBACK

        return True, [], text

    def sanitize(self, text: str) -> str:
        """Helper to return sanitized text."""
        _, _, safe_text = self.validate_message(text)
        return safe_text

# Singleton instance
safety_filter = SafetyFilter()

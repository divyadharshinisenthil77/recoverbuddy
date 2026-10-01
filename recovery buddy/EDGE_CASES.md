# Edge Cases & Failure Mode Handling: RecoverBuddy

This document outlines the 10 critical edge and failure cases specified in Section 38, detailing expected platform behavior, architectural mitigations, and automated test coverage.

---

## Edge Case Matrix

| Case # | Scenario | Challenge / Risk | Expected Platform Behavior | Automated Test Reference |
|---|---|---|---|---|
| **Case 1** | **Patient stops reporting** | Patient abandons check-ins silently; risk of unnoticed post-op deterioration | Detect missing daily record; dispatch friendly non-punitive reminder; if persistent for 3 days, create staff follow-up | `test_edge_cases.py::test_case_1_patient_stops_reporting` |
| **Case 2** | **Conflicting observations** | Patient selects `improving` wound, but writes *"incision is leaking yellow pus"* in notes | Detect keyword discrepancy (`pus`, `leak`); do not resolve automatically; trigger `CONFLICTING_OBSERVATION` task | `test_edge_cases.py::test_case_2_conflicting_observations` |
| **Case 3** | **Repeated missing data** | Patient ignores consecutive reminders; spamming pushes leads to app deletion | Halt repeated notifications via fatigue throttle; escalate to Care Coordinator for direct phone outreach | `test_edge_cases.py::test_case_3_repeated_missing_data` |
| **Case 4** | **Education ignored** | Patient completes daily pain check-ins but skips learning cards | Track education non-completion separately; do not penalize daily reporting streak; present micro-summaries | `test_edge_cases.py::test_case_4_education_ignored` |
| **Case 5** | **Notification delivery failure** | SMS/push fails due to carrier or device disconnect | Retry up to 3 times; if delivery permanently fails, spawn `NOTIFICATION_DELIVERY_FAILURE` follow-up | `test_edge_cases.py::test_case_5_notification_failure` |
| **Case 6** | **Out-of-range input** | Patient enters invalid data (e.g., Pain = 15, Temp = 55°C) | Pydantic v2 schema rejects payload with HTTP 422 error; explains valid range (Pain: 0–10, Temp: 34–43°C) | `test_edge_cases.py::test_case_6_out_of_range_input` |
| **Case 7** | **Duplicate submission** | Patient clicks submit twice within seconds | Deduplicate timestamps and store records with unique IDs; prevent artificial engagement inflation | `test_edge_cases.py::test_case_7_duplicate_submission` |
| **Case 8** | **Missing temperature** | Patient does not own a thermometer or omits temperature reading | Temperature remains `None`; trend engine outputs *"Not enough recent temperature data"* without hallucinating | `test_edge_cases.py::test_case_8_missing_temperature` |
| **Case 9** | **Noisy / outlier observation** | Sudden isolated pain spike (e.g. 4 ➔ 9) due to temporary morning stiffness | Acknowledge pain increase in feedback; flag for nurse review without diagnosing complication | `test_edge_cases.py::test_case_9_noisy_outlier_observation` |
| **Case 10** | **Patient returns after inactivity** | Patient resumes reporting after 5 days of absence | Display friendly welcome: *"Welcome back! You can continue from today."* Streak restarts without shame | `test_edge_cases.py::test_case_10_patient_returns_after_inactivity` |

---

## Verification Summary
All 10 edge cases have dedicated automated tests in `tests/test_edge_cases.py` and passed with **100% success rate**.

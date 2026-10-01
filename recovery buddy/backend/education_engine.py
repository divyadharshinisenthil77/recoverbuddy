"""
Education Engine for RecoverBuddy.
Provides plain-language recovery learning modules, interactive comprehension quizzes,
and measurable comprehension tracking for longitudinal experiment analytics.
"""
from typing import List, Dict, Any, Optional
from backend.schemas import (
    EducationModule, EducationQuizQuestion, EducationQuizSubmission, EducationQuizResult
)

EDUCATION_MODULES: List[EducationModule] = [
    EducationModule(
        module_id="why_checkins_matter",
        title="Why Daily Check-Ins Matter",
        summary="Learn how regular updates help your surgical care team keep your recovery on track.",
        icon="📊",
        points=[
            "Daily check-ins give your care team a clear day-to-day picture of your recovery journey.",
            "Spotting gradual changes early is much easier when you log observations consistently.",
            "Your updates help your care team know when everything is going well without unnecessary clinic trips."
        ],
        quiz=[
            EducationQuizQuestion(
                question_id="q1_1",
                question="Why is logging daily updates helpful for your surgical team?",
                options=[
                    "It helps them see your recovery trends and gradual changes over time.",
                    "It automatically diagnoses any medical condition without a doctor.",
                    "It replaces all future follow-up clinic visits permanently."
                ],
                correct_option_index=0,
                explanation="Logging daily helps your clinical team follow your longitudinal progress."
            ),
            EducationQuizQuestion(
                question_id="q1_2",
                question="What should you do if you forget to check in for a day?",
                options=[
                    "Stop logging completely.",
                    "Simply resume logging your updates the next day as usual.",
                    "Double all your medication doses."
                ],
                correct_option_index=1,
                explanation="There is no penalty for missed days; simply resume your check-in."
            )
        ]
    ),
    EducationModule(
        module_id="pain_tracking_basics",
        title="Understanding Pain Tracking",
        summary="How to use the 0 to 10 scale effectively so your clinicians understand your comfort level.",
        icon="📈",
        points=[
            "The pain scale ranges from 0 (no pain at all) to 10 (the most severe pain you can imagine).",
            "Rate your average pain level during your daily activities rather than just a brief moment.",
            "Sharing your pain score regularly helps your team understand if your recovery comfort is improving."
        ],
        quiz=[
            EducationQuizQuestion(
                question_id="q2_1",
                question="What does a score of 0 represent on the pain scale?",
                options=[
                    "Moderate discomfort",
                    "No pain at all",
                    "Severe pain requiring hospital admission"
                ],
                correct_option_index=1,
                explanation="0 indicates no pain, while 10 represents the most severe pain."
            ),
            EducationQuizQuestion(
                question_id="q2_2",
                question="Does RecoverBuddy change your medication dose if your pain score increases?",
                options=[
                    "Yes, it automatically prescribes new painkillers.",
                    "No, it flags the change for your human care team to evaluate.",
                    "No, it ignores the score completely."
                ],
                correct_option_index=1,
                explanation="RecoverBuddy never alters medication; it alerts your human care team."
            )
        ]
    ),
    EducationModule(
        module_id="temp_tracking_guide",
        title="Recording Temperature Correctly",
        summary="Best practices for taking and logging an accurate body temperature reading.",
        icon="🌡️",
        points=[
            "Wait at least 20 minutes after drinking hot or cold liquids before taking an oral temperature.",
            "Log your reading in degrees Celsius (°C). Normal resting body temperature is typically around 36.5°C to 37.5°C.",
            "If your temperature reaches 38.0°C or higher, the system alerts your care team for follow-up review."
        ],
        quiz=[
            EducationQuizQuestion(
                question_id="q3_1",
                question="How long should you wait after hot or cold drinks before taking oral temperature?",
                options=[
                    "At least 20 minutes",
                    "No wait time is needed",
                    "At least 4 hours"
                ],
                correct_option_index=0,
                explanation="Waiting 20 minutes prevents oral liquid temperature from skewing readings."
            )
        ]
    ),
    EducationModule(
        module_id="wound_observation",
        title="Wound Observation Basics",
        summary="Simple guidelines for observing and reporting how your surgical incision looks.",
        icon="🩹",
        points=[
            "Observe your surgical incision daily in good lighting.",
            "Report whether the area looks improving, unchanged, or concerning.",
            "If you select 'concerning', your report is directly placed on your nurse's review queue."
        ],
        quiz=[
            EducationQuizQuestion(
                question_id="q4_1",
                question="What happens when you select 'concerning' for your wound observation?",
                options=[
                    "The app diagnoses an infection automatically.",
                    "A human healthcare professional from your care team is notified to review it.",
                    "The app deletes your record."
                ],
                correct_option_index=1,
                explanation="Concerning observations create a clinical follow-up task for healthcare staff."
            )
        ]
    ),
    EducationModule(
        module_id="medication_adherence",
        title="Medication Adherence Reminders",
        summary="Why taking prescribed medications on schedule supports healing and comfort.",
        icon="💊",
        points=[
            "Take your prescribed recovery medications as directed by your surgeon and pharmacy.",
            "Use the daily check-in to confirm when medications were taken on schedule.",
            "Never stop or adjust prescribed dosages without consulting your doctor or nurse."
        ],
        quiz=[
            EducationQuizQuestion(
                question_id="q5_1",
                question="Who should decide if a change to your prescribed medication is needed?",
                options=[
                    "An automated mobile app",
                    "Your doctor, surgeon, or licensed healthcare provider",
                    "Social media forums"
                ],
                correct_option_index=1,
                explanation="Only licensed clinicians can authorize prescription medication adjustments."
            )
        ]
    ),
    EducationModule(
        module_id="when_to_contact_team",
        title="When to Contact Your Care Team",
        summary="Clear guidance on routine app reporting versus calling clinical staff directly.",
        icon="🏥",
        points=[
            "The app is designed for daily recovery tracking, not for emergency response.",
            "For unexpected severe symptoms (such as sudden chest pain or shortness of breath), call emergency services immediately.",
            "For ongoing recovery questions, message or call your hospital recovery contact number."
        ],
        quiz=[
            EducationQuizQuestion(
                question_id="q6_1",
                question="Is RecoverBuddy an emergency medical dispatch service?",
                options=[
                    "No, for medical emergencies you must call local emergency services immediately.",
                    "Yes, it replaces emergency response teams."
                ],
                correct_option_index=0,
                explanation="RecoverBuddy is an engagement and tracking tool, not an emergency dispatcher."
            )
        ]
    ),
    EducationModule(
        module_id="caregiver_support",
        title="How Caregivers Can Help",
        summary="Empowering family members and caregivers to assist with check-ins and recovery goals.",
        icon="🤝",
        points=[
            "Caregivers can help patients log check-ins if the patient feels fatigued.",
            "Encouraging gentle mobility and hydration helps maintain positive daily routines.",
            "Caregivers can review education modules together with the patient."
        ],
        quiz=[
            EducationQuizQuestion(
                question_id="q7_1",
                question="Can a designated caregiver assist a patient with daily check-in reporting?",
                options=[
                    "Yes, caregivers can support patients by assisting with daily check-ins.",
                    "No, only doctors are allowed to touch the phone."
                ],
                correct_option_index=0,
                explanation="Caregiver support is a proven factor in sustaining post-op engagement."
            )
        ]
    )
]

class EducationEngine:
    def __init__(self):
        self._modules_map: Dict[str, EducationModule] = {m.module_id: m for m in EDUCATION_MODULES}

    def get_all_modules(self) -> List[EducationModule]:
        return EDUCATION_MODULES

    def get_module(self, module_id: str) -> Optional[EducationModule]:
        return self._modules_map.get(module_id)

    def evaluate_quiz(self, submission: EducationQuizSubmission) -> EducationQuizResult:
        """
        Evaluates submitted quiz answers and returns a Comprehension score.
        """
        module = self._modules_map.get(submission.module_id)
        if not module:
            raise ValueError(f"Module '{submission.module_id}' not found.")

        total_questions = len(module.quiz)
        if total_questions == 0:
            return EducationQuizResult(
                module_id=submission.module_id,
                score_percentage=100.0,
                passed=True,
                correct_count=0,
                total_questions=0,
                feedback="Module completed."
            )

        correct_count = 0
        for q in module.quiz:
            selected_answer = submission.answers.get(q.question_id)
            if selected_answer is not None and selected_answer == q.correct_option_index:
                correct_count += 1

        score_pct = round((correct_count / total_questions) * 100.0, 1)
        passed = score_pct >= 60.0

        feedback = (
            f"Great job! You answered {correct_count} of {total_questions} questions correctly ({score_pct}%)."
            if passed else
            f"You got {correct_count} of {total_questions} questions correct. Review the module points to learn more."
        )

        return EducationQuizResult(
            module_id=submission.module_id,
            score_percentage=score_pct,
            passed=passed,
            correct_count=correct_count,
            total_questions=total_questions,
            feedback=feedback
        )

education_engine = EducationEngine()

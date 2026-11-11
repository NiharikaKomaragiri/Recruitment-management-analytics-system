import random

from config import RANDOM_SEED


RECOMMENDATIONS = [
    "STRONG_HIRE",
    "HIRE",
    "NEUTRAL",
    "NO_HIRE",
    "STRONG_NO_HIRE",
]


class FeedbackGenerator:

    def generate(self, interviews, panel_assignments):

        rng = random.Random(RANDOM_SEED)

        completed_ids = {
            i["interview_id"]
            for i in interviews
            if i["status"] == "COMPLETED"
        }

        feedback_records = []

        for panel in panel_assignments:

            interview_id = panel["interview_business_id"]

            # Feedback is submitted only after completed interviews.
            if interview_id not in completed_ids:
                continue

            interviewer_id = panel["interviewer_business_id"]

            scores = {
                "technical_score": round(rng.uniform(4, 10), 1),
                "communication_score": round(rng.uniform(4, 10), 1),
                "problem_solving_score": round(rng.uniform(4, 10), 1),
                "cultural_fit_score": round(rng.uniform(4, 10), 1),
            }

            overall = round(sum(scores.values()) / 4, 1)

            recommendation = (
                "STRONG_HIRE" if overall >= 9
                else "HIRE" if overall >= 7.5
                else "NEUTRAL" if overall >= 6
                else "NO_HIRE" if overall >= 5
                else "STRONG_NO_HIRE"
            )

            feedback_records.append({
                "feedback_id": f"FB-{interview_id}-{interviewer_id}",
                "interview_business_id": interview_id,
                "interviewer_business_id": interviewer_id,
                **scores,
                "overall_score": overall,
                "recommendation": recommendation,
                "strengths": "Demonstrated relevant skills and knowledge.",
                "areas_for_improvement": "Continue developing technical depth.",
                "comments": "Synthetic structured interview feedback.",
            })

        return {"feedback": feedback_records}
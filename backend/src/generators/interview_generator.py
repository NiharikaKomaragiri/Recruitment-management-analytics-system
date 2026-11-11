import random
from datetime import datetime, timedelta

from config import RANDOM_SEED, SCALE_CONFIG


ROUNDS = [
    "SCREENING",
    "TECHNICAL_1",
    "TECHNICAL_2",
    "SYSTEM_DESIGN",
    "BEHAVIORAL",
    "MANAGERIAL",
    "HR_FINAL",
]

MODES = ["VIDEO", "IN_PERSON", "PHONE"]

STATUSES = ["SCHEDULED", "CONFIRMED", "COMPLETED"]


class InterviewGenerator:

    def generate(self, applications, interviewers, scale="medium"):

        rng = random.Random(RANDOM_SEED)

        target = SCALE_CONFIG[scale]["num_interviews"]

        eligible = [
            a for a in applications
            if a["current_stage"] in [
                "SHORTLISTED", "INTERVIEW", "ASSESSMENT", "OFFER"
            ]
        ]

        if len(eligible) < target:
            raise ValueError(
                f"Need {target} eligible applications; found {len(eligible)}"
            )

        if len(interviewers) < 2:
            raise ValueError("At least two interviewers are required.")

        selected_apps = rng.sample(eligible, target)

        # Track interviewer weekly workload and occupied time slots.
        weekly_load = {}
        occupied_slots = {}

        interviews = []
        panel_assignments = []

        start_date = datetime(2026, 1, 5, 9, 0)

        for number, app in enumerate(selected_apps, start=1):

            interview_id = f"INT-2026-{number:06d}"

            # Find a slot with two available interviewers.
            scheduled = False

            for day_offset in range(180):
                day = start_date + timedelta(days=day_offset)

                if day.weekday() >= 5:
                    continue

                for hour in [9, 10, 11, 13, 14, 15, 16]:

                    start = day.replace(hour=hour)
                    end = start + timedelta(minutes=60)

                    available = []

                    week_key = start.isocalendar()[:2]

                    for interviewer in interviewers:
                        iid = interviewer["interviewer_id"]

                        if weekly_load.get((iid, week_key), 0) >= 5:
                            continue

                        slot_key = (iid, start)

                        if slot_key not in occupied_slots:
                            available.append(interviewer)

                    if len(available) >= 2:
                        chosen = rng.sample(available, 2)

                        for interviewer in chosen:
                            iid = interviewer["interviewer_id"]

                            weekly_load[(iid, week_key)] = (
                                weekly_load.get((iid, week_key), 0) + 1
                            )

                            occupied_slots[(iid, start)] = interview_id

                        scheduled = True
                        break

                if scheduled:
                    break

            if not scheduled:
                raise RuntimeError(
                    f"Could not schedule interview {interview_id}"
                )

            # Select the interview mode only once.
            mode = rng.choice(MODES)

            interviews.append({
                "interview_id": interview_id,
                "application_business_id": app["application_id"],
                "round_number": 1,
                "round_name": rng.choice(ROUNDS),
                "scheduled_start": start,
                "scheduled_end": end,
                "mode": mode,
                "location_or_meeting_link": (
                    "https://meet.example.test/" + interview_id
                    if mode == "VIDEO"
                    else "Hyderabad Office"
                ),
                "status": rng.choice(STATUSES),
            })

            # Assign two interviewers to the interview.
            for index, interviewer in enumerate(chosen):

                panel_assignments.append({
                    "interview_business_id": interview_id,
                    "interviewer_business_id": interviewer["interviewer_id"],
                    "role": "LEAD" if index == 0 else "PANELIST",
                    "confirmed": True,
                })

        return {
            "interviews": interviews,
            "panel_assignments": panel_assignments,
        }
from collections import defaultdict
from ortools.sat.python import cp_model


PRIORITY_WEIGHT = {
    "Emergency": 1000,
    "Critical": 800,
    "High": 500,
    "Normal": 200,
    "Low": 100,
}


def optimize_schedule(surgeries, operating_rooms):
    """
    SurgiPlan OR-Tools scheduling engine.

    Constraints:
    - Surgery can only use a compatible OR.
    - A surgery can use only one OR.
    - Surgeries cannot overlap in the same OR.
    - A surgeon cannot perform overlapping surgeries.
    - An anesthetist cannot support overlapping surgeries.
    - Surgeries must fit inside the scheduling horizon.
    - Higher-priority surgeries are preferred.

    OR-Tools is the source of truth for scheduling.
    """

    model = cp_model.CpModel()

    horizon = 600  # 08:00 - 18:00

    scheduled_vars = {}
    start_vars = {}
    end_vars = {}
    room_assignment_vars = {}

    intervals_by_room = defaultdict(list)
    intervals_by_surgeon = defaultdict(list)
    intervals_by_anesthetist = defaultdict(list)

    # ---------------------------------------------------------
    # Create surgery variables
    # ---------------------------------------------------------

    for surgery in surgeries:

        surgery_id = surgery.id

        scheduled = model.NewBoolVar(
            f"scheduled_{surgery_id}"
        )

        start = model.NewIntVar(
            0,
            horizon,
            f"start_{surgery_id}"
        )

        end = model.NewIntVar(
            0,
            horizon,
            f"end_{surgery_id}"
        )

        scheduled_vars[surgery_id] = scheduled
        start_vars[surgery_id] = start
        end_vars[surgery_id] = end

        # End = start + duration
        model.Add(
            end == start + surgery.duration
        ).OnlyEnforceIf(scheduled)

        # Surgery must finish within the working day.
        model.Add(
            start + surgery.duration <= horizon
        ).OnlyEnforceIf(scheduled)

        assignments = []

        # -----------------------------------------------------
        # OR assignment
        # -----------------------------------------------------

        for room_index, room in enumerate(operating_rooms):

            # Only compatible specialties can use this OR.
            if surgery.specialty not in room.specialties:
                continue

            assignment = model.NewBoolVar(
                f"{surgery_id}_uses_{room.id}"
            )

            assignments.append(assignment)

            room_assignment_vars[
                (surgery_id, room_index)
            ] = assignment

            interval = model.NewOptionalIntervalVar(
                start,
                surgery.duration,
                end,
                assignment,
                f"interval_{surgery_id}_{room.id}"
            )

            intervals_by_room[room_index].append(
                interval
            )

        # Exactly one compatible OR if scheduled.
        model.Add(
            sum(assignments) == scheduled
        )

        # -----------------------------------------------------
        # Surgeon resource interval
        # -----------------------------------------------------

        surgeon_interval = model.NewOptionalIntervalVar(
            start,
            surgery.duration,
            end,
            scheduled,
            f"surgeon_{surgery_id}"
        )

        intervals_by_surgeon[
            surgery.surgeon
        ].append(surgeon_interval)

        # -----------------------------------------------------
        # Anesthetist resource interval
        # -----------------------------------------------------

        anesthetist_interval = model.NewOptionalIntervalVar(
            start,
            surgery.duration,
            end,
            scheduled,
            f"anesthetist_{surgery_id}"
        )

        intervals_by_anesthetist[
            surgery.anesthetist
        ].append(anesthetist_interval)

    # ---------------------------------------------------------
    # OR overlap constraints
    # ---------------------------------------------------------

    for room_index, intervals in intervals_by_room.items():

        model.AddNoOverlap(intervals)

    # ---------------------------------------------------------
    # Surgeon overlap constraints
    # ---------------------------------------------------------

    for surgeon, intervals in intervals_by_surgeon.items():

        model.AddNoOverlap(intervals)

    # ---------------------------------------------------------
    # Anesthetist overlap constraints
    # ---------------------------------------------------------

    for anesthetist, intervals in intervals_by_anesthetist.items():

        model.AddNoOverlap(intervals)

    # ---------------------------------------------------------
    # Objective
    # ---------------------------------------------------------

    objective_terms = []

    for surgery in surgeries:

        surgery_id = surgery.id
        scheduled = scheduled_vars[surgery_id]

        priority_weight = PRIORITY_WEIGHT.get(
            surgery.priority,
            100
        )

        # Reward scheduling higher-priority surgeries.
        objective_terms.append(
            priority_weight * scheduled
        )

        # Prefer earlier start times.
        early_start = model.NewIntVar(
            0,
            horizon,
            f"early_start_{surgery_id}"
        )

        model.Add(
            early_start == start_vars[surgery_id]
        ).OnlyEnforceIf(scheduled)

        model.Add(
            early_start == horizon
        ).OnlyEnforceIf(scheduled.Not())

        objective_terms.append(
            horizon - early_start
        )

    model.Maximize(
        sum(objective_terms)
    )

    # ---------------------------------------------------------
    # Solve
    # ---------------------------------------------------------

    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = 10
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)

    # ---------------------------------------------------------
    # Build result
    # ---------------------------------------------------------

    schedule = []
    unscheduled_surgeries = []

    if status in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ):

        for surgery in surgeries:

            surgery_id = surgery.id

            if not solver.Value(
                scheduled_vars[surgery_id]
            ):
                unscheduled_surgeries.append(
                    surgery_id
                )
                continue

            assigned_room = None

            for room_index, room in enumerate(
                operating_rooms
            ):

                assignment = room_assignment_vars.get(
                    (surgery_id, room_index)
                )

                if assignment is not None:

                    if solver.Value(assignment):
                        assigned_room = room
                        break

            if assigned_room is None:
                unscheduled_surgeries.append(
                    surgery_id
                )
                continue

            start = solver.Value(
                start_vars[surgery_id]
            )

            end = solver.Value(
                end_vars[surgery_id]
            )

            schedule.append({
                "surgery_id": surgery.id,
                "procedure": surgery.procedure,
                "specialty": surgery.specialty,
                "priority": surgery.priority,
                "surgeon": surgery.surgeon,
                "anesthetist": surgery.anesthetist,
                "room": assigned_room.id,
                "start": start,
                "end": end,
                "duration": surgery.duration,
            })

    else:

        unscheduled_surgeries = [
            surgery.id
            for surgery in surgeries
        ]

    return {
        "schedule": schedule,
        "unscheduled_surgeries": unscheduled_surgeries,
        "status": solver.StatusName(status),
    }
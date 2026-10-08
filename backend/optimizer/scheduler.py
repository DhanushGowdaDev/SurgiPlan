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
    Optimize surgery scheduling using Google OR-Tools CP-SAT.

    The solver decides:
    - whether a surgery is scheduled
    - which compatible OR it uses
    - when it starts

    OR-Tools is the source of truth for the schedule.
    """

    model = cp_model.CpModel()

    horizon = 600  # 08:00 - 18:00

    # ---------------------------------------------------------
    # Variables
    # ---------------------------------------------------------

    scheduled_vars = {}
    start_vars = {}
    end_vars = {}
    room_assignment_vars = {}

    # Optional interval variables:
    # intervals_by_room[room_index] contains all surgeries
    # that could potentially use that OR.
    intervals_by_room = {
        room_index: []
        for room_index in range(len(operating_rooms))
    }

    for surgery in surgeries:

        surgery_id = surgery.id

        # Whether the surgery gets scheduled at all.
        scheduled = model.NewBoolVar(
            f"scheduled_{surgery_id}"
        )

        scheduled_vars[surgery_id] = scheduled

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

        start_vars[surgery_id] = start
        end_vars[surgery_id] = end

        # End = start + duration
        model.Add(
            end == start + surgery.duration
        ).OnlyEnforceIf(scheduled)

        # Surgery must finish before the end of the day.
        model.Add(
            start + surgery.duration <= horizon
        ).OnlyEnforceIf(scheduled)

        assignments = []

        # -----------------------------------------------------
        # Create an optional interval for every compatible OR
        # -----------------------------------------------------

        for room_index, room in enumerate(operating_rooms):

            # Surgery can only use an OR that supports
            # its specialty.
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

        # A surgery can use at most one OR.
        model.Add(
            sum(assignments) == scheduled
        )

    # ---------------------------------------------------------
    # No overlapping surgeries in each OR
    # ---------------------------------------------------------

    for room_index in range(len(operating_rooms)):

        model.AddNoOverlap(
            intervals_by_room[room_index]
        )

    # ---------------------------------------------------------
    # Objective
    # ---------------------------------------------------------

    objective_terms = []

    for surgery in surgeries:

        surgery_id = surgery.id

        priority_weight = PRIORITY_WEIGHT.get(
            surgery.priority,
            100
        )

        scheduled = scheduled_vars[surgery_id]

        # Strongly reward scheduling higher-priority surgeries.
        objective_terms.append(
            priority_weight * scheduled
        )

        # Among otherwise similar solutions, prefer earlier
        # surgery start times.
        #
        # We use a helper variable because start time is only
        # meaningful when the surgery is scheduled.
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

            if solver.Value(
                scheduled_vars[surgery_id]
            ):

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

                unscheduled_surgeries.append(
                    surgery_id
                )

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
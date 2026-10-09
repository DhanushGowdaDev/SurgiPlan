
from collections import defaultdict
from ortools.sat.python import cp_model


PRIORITY_WEIGHT = {
    "Emergency": 1000,
    "Critical": 800,
    "High": 500,
    "Normal": 200,
    "Low": 100,
}


def optimize_schedule(surgeries, operating_rooms, equipment):
    """Optimize surgery scheduling using OR-Tools CP-SAT."""

    model = cp_model.CpModel()
    horizon = 600  # 08:00 to 18:00, in minutes

    scheduled_vars = {}
    start_vars = {}
    end_vars = {}
    room_assignment_vars = {}

    intervals_by_room = defaultdict(list)
    intervals_by_surgeon = defaultdict(list)
    intervals_by_anesthetist = defaultdict(list)
    intervals_by_equipment_type = defaultdict(list)

    # Count physical equipment units by type.
    equipment_capacity = defaultdict(int)
    for item in equipment:
        equipment_capacity[item.equipment_type] += 1

    # Create variables for every surgery.
    for surgery in surgeries:
        surgery_id = surgery.id

        scheduled = model.NewBoolVar(f"scheduled_{surgery_id}")
        start = model.NewIntVar(0, horizon, f"start_{surgery_id}")
        end = model.NewIntVar(0, horizon, f"end_{surgery_id}")

        scheduled_vars[surgery_id] = scheduled
        start_vars[surgery_id] = start
        end_vars[surgery_id] = end

        # A scheduled surgery must finish within the horizon.
        model.Add(
            end == start + surgery.duration
        ).OnlyEnforceIf(scheduled)

        model.Add(
            start + surgery.duration <= horizon
        ).OnlyEnforceIf(scheduled)

        # Operating-room assignment: exactly one compatible OR
        # if scheduled; zero ORs otherwise.
        assignments = []

        for room_index, room in enumerate(operating_rooms):
            if surgery.specialty not in room.specialties:
                continue

            assignment = model.NewBoolVar(
                f"{surgery_id}_uses_{room.id}"
            )
            assignments.append(assignment)
            room_assignment_vars[(surgery_id, room_index)] = assignment

            interval = model.NewOptionalIntervalVar(
                start,
                surgery.duration,
                end,
                assignment,
                f"room_{surgery_id}_{room.id}",
            )
            intervals_by_room[room_index].append(interval)

        model.Add(sum(assignments) == scheduled)

        # Surgeon cannot perform overlapping surgeries.
        surgeon_interval = model.NewOptionalIntervalVar(
            start,
            surgery.duration,
            end,
            scheduled,
            f"surgeon_{surgery_id}",
        )
        intervals_by_surgeon[surgery.surgeon].append(surgeon_interval)

        # Anesthetist cannot support overlapping surgeries.
        anesthetist_interval = model.NewOptionalIntervalVar(
            start,
            surgery.duration,
            end,
            scheduled,
            f"anesthetist_{surgery_id}",
        )
        intervals_by_anesthetist[surgery.anesthetist].append(
            anesthetist_interval
        )

        # Each required equipment type consumes one unit
        # for the entire duration of the surgery.
        for equipment_type in surgery.required_equipment:
            if equipment_capacity[equipment_type] == 0:
                # Cannot schedule surgery if equipment is missing.
                model.Add(scheduled == 0)
                continue

            equipment_interval = model.NewOptionalIntervalVar(
                start,
                surgery.duration,
                end,
                scheduled,
                f"equipment_{equipment_type}_{surgery_id}",
            )
            intervals_by_equipment_type[equipment_type].append(
                equipment_interval
            )

    # Resource constraints.
    for intervals in intervals_by_room.values():
        model.AddNoOverlap(intervals)

    for intervals in intervals_by_surgeon.values():
        model.AddNoOverlap(intervals)

    for intervals in intervals_by_anesthetist.values():
        model.AddNoOverlap(intervals)

    # Capacity permits as many simultaneous users as there
    # are physical units of each equipment type.
    for equipment_type, intervals in intervals_by_equipment_type.items():
        model.AddCumulative(
            intervals,
            [1] * len(intervals),
            equipment_capacity[equipment_type],
        )

    # Objective: prioritize surgeries and prefer earlier starts.
    objective_terms = []

    for surgery in surgeries:
        surgery_id = surgery.id
        scheduled = scheduled_vars[surgery_id]

        weight = PRIORITY_WEIGHT.get(surgery.priority, 100)
        objective_terms.append(weight * scheduled)

        early_start = model.NewIntVar(
            0, horizon, f"early_start_{surgery_id}"
        )

        model.Add(
            early_start == start_vars[surgery_id]
        ).OnlyEnforceIf(scheduled)

        model.Add(
            early_start == horizon
        ).OnlyEnforceIf(scheduled.Not())

        objective_terms.append(horizon - early_start)

    model.Maximize(sum(objective_terms))

    # Solve the model.
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    # Build the result.
    schedule = []
    unscheduled_surgeries = []

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for surgery in surgeries:
            surgery_id = surgery.id

            if not solver.Value(scheduled_vars[surgery_id]):
                unscheduled_surgeries.append(surgery_id)
                continue

            assigned_room = None

            for room_index, room in enumerate(operating_rooms):
                assignment = room_assignment_vars.get(
                    (surgery_id, room_index)
                )

                if assignment is not None and solver.Value(assignment):
                    assigned_room = room
                    break

            if assigned_room is None:
                unscheduled_surgeries.append(surgery_id)
                continue

            start = solver.Value(start_vars[surgery_id])
            end = solver.Value(end_vars[surgery_id])

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
                "required_equipment": list(
                    surgery.required_equipment
                ),
            })
    else:
        unscheduled_surgeries = [
            surgery.id for surgery in surgeries
        ]

    return {
        "schedule": schedule,
        "unscheduled_surgeries": unscheduled_surgeries,
        "status": solver.StatusName(status),
    }


from collections import defaultdict
from ortools.sat.python import cp_model


PRIORITY_WEIGHT = {
    "Emergency": 1000,
    "Critical": 800,
    "High": 500,
    "Normal": 200,
    "Low": 100,
}


def optimize_schedule(
    surgeries,
    operating_rooms,
    equipment,
    staff=None,
    recovery_beds=None,
):
    """Optimize surgeries with room, staff, equipment and recovery constraints."""

    model = cp_model.CpModel()
    horizon = 600  # 08:00 to 18:00

    scheduled_vars = {}
    start_vars = {}
    end_vars = {}
    room_assignment_vars = {}

    intervals_by_room = defaultdict(list)
    intervals_by_surgeon = defaultdict(list)
    intervals_by_anesthetist = defaultdict(list)
    intervals_by_equipment_type = defaultdict(list)
    recovery_intervals = []
    recovery_demands = []

    equipment_capacity = defaultdict(int)
    for item in equipment:
        equipment_capacity[item.equipment_type] += 1

    staff_by_id = {
        member.id: member for member in (staff or [])
    }

    recovery_capacity = None
    if recovery_beds is not None:
        recovery_capacity = sum(
            1 for bed in recovery_beds if bed.available
        )

    max_recovery_duration = max(
        (s.recovery_duration for s in surgeries),
        default=0,
    )
    recovery_horizon = horizon + max_recovery_duration

    # Create scheduling variables.
    for surgery in surgeries:
        surgery_id = surgery.id

        if surgery.duration <= 0:
            raise ValueError(
                f"Surgery {surgery_id} must have a positive duration."
            )

        if surgery.recovery_duration <= 0:
            raise ValueError(
                f"Surgery {surgery_id} must have a positive recovery duration."
            )

        if surgery.recovery_beds < 0:
            raise ValueError(
                f"Surgery {surgery_id} cannot require negative recovery beds."
            )

        scheduled = model.NewBoolVar(f"scheduled_{surgery_id}")
        start = model.NewIntVar(0, horizon, f"start_{surgery_id}")
        end = model.NewIntVar(0, horizon, f"end_{surgery_id}")

        scheduled_vars[surgery_id] = scheduled
        start_vars[surgery_id] = start
        end_vars[surgery_id] = end

        model.Add(
            end == start + surgery.duration
        ).OnlyEnforceIf(scheduled)

        model.Add(
            start + surgery.duration <= horizon
        ).OnlyEnforceIf(scheduled)

        # Surgeon and anesthetist availability.
        if staff is not None:
            required_staff = [
                (surgery.surgeon, "surgeon"),
                (surgery.anesthetist, "anesthetist"),
            ]

            for staff_id, expected_role in required_staff:
                member = staff_by_id.get(staff_id)

                if member is None or member.role != expected_role:
                    model.Add(scheduled == 0)
                    continue

                if not (
                    0 <= member.available_start
                    < member.available_end <= horizon
                ):
                    raise ValueError(
                        f"Invalid working hours for {staff_id}."
                    )

                model.Add(
                    start >= member.available_start
                ).OnlyEnforceIf(scheduled)

                model.Add(
                    end <= member.available_end
                ).OnlyEnforceIf(scheduled)

        # Assign each scheduled surgery to exactly one compatible OR.
        assignments = []

        for room_index, room in enumerate(operating_rooms):
            if surgery.specialty not in room.specialties:
                continue

            assignment = model.NewBoolVar(
                f"{surgery_id}_uses_{room.id}"
            )
            assignments.append(assignment)
            room_assignment_vars[(surgery_id, room_index)] = assignment

            if not (
                0 <= room.available_start
                < room.available_end <= horizon
            ):
                raise ValueError(
                    f"Invalid working hours for {room.id}."
                )

            model.Add(
                start >= room.available_start
            ).OnlyEnforceIf(assignment)

            model.Add(
                end <= room.available_end
            ).OnlyEnforceIf(assignment)

            room_interval = model.NewOptionalIntervalVar(
                start,
                surgery.duration,
                end,
                assignment,
                f"room_{surgery_id}_{room.id}",
            )
            intervals_by_room[room_index].append(room_interval)

        model.Add(sum(assignments) == scheduled)

        # Prevent surgeon and anesthetist double-booking.
        surgeon_interval = model.NewOptionalIntervalVar(
            start,
            surgery.duration,
            end,
            scheduled,
            f"surgeon_{surgery_id}",
        )
        intervals_by_surgeon[surgery.surgeon].append(surgeon_interval)

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

        # Equipment capacity constraints.
        for equipment_type in surgery.required_equipment:
            if equipment_capacity[equipment_type] == 0:
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

        # Recovery starts when the surgery finishes.
        # Each surgery occupies its requested number of beds
        # for its recovery duration.
        if recovery_capacity is not None:
            recovery_end = model.NewIntVar(
                0,
                recovery_horizon,
                f"recovery_end_{surgery_id}",
            )

            recovery_interval = model.NewOptionalIntervalVar(
                end,
                surgery.recovery_duration,
                recovery_end,
                scheduled,
                f"recovery_{surgery_id}",
            )

            recovery_intervals.append(recovery_interval)
            recovery_demands.append(surgery.recovery_beds)

    # Add room maintenance intervals.
    for room_index, room in enumerate(operating_rooms):
        for period_index, period in enumerate(room.unavailable_periods):
            maintenance_start = period["start"]
            maintenance_end = period["end"]

            if not (
                room.available_start <= maintenance_start
                < maintenance_end <= room.available_end
            ):
                raise ValueError(
                    f"Invalid maintenance period for {room.id}: {period}"
                )

            maintenance_interval = model.NewIntervalVar(
                maintenance_start,
                maintenance_end - maintenance_start,
                maintenance_end,
                f"maintenance_{room.id}_{period_index}",
            )
            intervals_by_room[room_index].append(maintenance_interval)

    # Operating-room, maintenance and staff conflict constraints.
    for intervals in intervals_by_room.values():
        model.AddNoOverlap(intervals)

    for intervals in intervals_by_surgeon.values():
        model.AddNoOverlap(intervals)

    for intervals in intervals_by_anesthetist.values():
        model.AddNoOverlap(intervals)

    # Limit simultaneous use of each equipment type.
    for equipment_type, intervals in intervals_by_equipment_type.items():
        model.AddCumulative(
            intervals,
            [1] * len(intervals),
            equipment_capacity[equipment_type],
        )

    # Limit simultaneous recovery demand to available beds.
    if recovery_capacity is not None and recovery_intervals:
        model.AddCumulative(
            recovery_intervals,
            recovery_demands,
            recovery_capacity,
        )

    # Maximize priority-weighted scheduling and favor earlier starts.
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

    # Solve the optimization model.
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

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
                "recovery_start": end,
                "recovery_end": end + surgery.recovery_duration,
                "recovery_duration": surgery.recovery_duration,
                "recovery_beds": surgery.recovery_beds,
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
        "recovery_bed_capacity": recovery_capacity,
    }

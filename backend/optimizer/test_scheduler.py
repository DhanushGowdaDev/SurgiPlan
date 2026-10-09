
from data.demo_data import create_demo_data
from optimizer.scheduler import optimize_schedule


def validate_recovery_capacity(schedule, capacity):
    events = []

    for item in schedule:
        demand = item["recovery_beds"]

        if demand == 0:
            continue

        events.append((item["recovery_start"], demand))
        events.append((item["recovery_end"], -demand))

    # Process recovery endings before starts at the same minute.
    events.sort(key=lambda event: (event[0], event[1]))

    occupied = 0

    for minute, change in events:
        occupied += change

        assert occupied >= 0, (
            f"Invalid recovery-bed occupancy at minute {minute}."
        )
        assert occupied <= capacity, (
            f"Recovery capacity exceeded at minute {minute}: "
            f"{occupied}/{capacity} beds."
        )


def validate_schedule(result, data, capacity):
    assert result["status"] in ("OPTIMAL", "FEASIBLE"), (
        f"Solver did not find a solution: {result['status']}"
    )

    rooms_by_id = {
        room.id: room for room in data["operating_rooms"]
    }
    staff_by_id = {
        member.id: member for member in data["staff"]
    }

    # Check room availability and maintenance.
    for item in result["schedule"]:
        room = rooms_by_id[item["room"]]
        start = item["start"]
        end = item["end"]

        assert start >= room.available_start
        assert end <= room.available_end

        for period in room.unavailable_periods:
            assert not (
                start < period["end"] and end > period["start"]
            ), f"{item['surgery_id']} overlaps room maintenance."

        # Check surgeon and anesthetist working hours.
        for staff_id in (item["surgeon"], item["anesthetist"]):
            member = staff_by_id[staff_id]

            assert start >= member.available_start
            assert end <= member.available_end

    # Check no overlapping surgeries in each room.
    for room in data["operating_rooms"]:
        items = sorted(
            [
                item for item in result["schedule"]
                if item["room"] == room.id
            ],
            key=lambda item: item["start"],
        )

        for previous, current in zip(items, items[1:]):
            assert previous["end"] <= current["start"], (
                f"Overlapping surgeries in {room.id}."
            )

    # Check no overlapping assignments for each staff member.
    for field in ("surgeon", "anesthetist"):
        by_person = {}

        for item in result["schedule"]:
            by_person.setdefault(item[field], []).append(item)

        for staff_id, items in by_person.items():
            items.sort(key=lambda item: item["start"])

            for previous, current in zip(items, items[1:]):
                assert previous["end"] <= current["start"], (
                    f"{staff_id} has overlapping surgeries."
                )

    # Check total recovery-bed occupancy.
    validate_recovery_capacity(result["schedule"], capacity)


def main():
    data = create_demo_data()

    # Maintenance in OR-2: 10:00 AM to 12:00 PM.
    or2 = next(
        room for room in data["operating_rooms"]
        if room.id == "OR-2"
    )
    or2.unavailable_periods = [
        {"start": 120, "end": 240}
    ]

    # Restrict Dr. Patel's working hours for testing.
    surgeon = next(
        member for member in data["staff"]
        if member.id == "Dr. Patel"
    )
    surgeon.available_start = 60
    surgeon.available_end = 300

    # Test the normal capacity of 15 recovery beds.
    normal_beds = data["recovery_beds"]

    result = optimize_schedule(
        data["surgeries"],
        data["operating_rooms"],
        data["equipment"],
        data["staff"],
        normal_beds,
    )

    normal_capacity = sum(
        1 for bed in normal_beds if bed.available
    )

    validate_schedule(result, data, normal_capacity)

    print("\n==============================")
    print("SURGIPLAN RECOVERY CAPACITY TEST")
    print("==============================")
    print("Solver status:", result["status"])
    print("Recovery capacity:", normal_capacity)
    print("Scheduled:", len(result["schedule"]))
    print("Unscheduled:", len(result["unscheduled_surgeries"]))
    print("15-bed capacity check passed.")

    # Simulate a reduction to three available recovery beds.
    reduced_beds = normal_beds[:3]

    reduced_result = optimize_schedule(
        data["surgeries"],
        data["operating_rooms"],
        data["equipment"],
        data["staff"],
        reduced_beds,
    )

    reduced_capacity = sum(
        1 for bed in reduced_beds if bed.available
    )

    validate_schedule(reduced_result, data, reduced_capacity)

    print("\nReduced recovery capacity:", reduced_capacity)
    print("Scheduled:", len(reduced_result["schedule"]))
    print("Unscheduled:", len(reduced_result["unscheduled_surgeries"]))
    print("3-bed capacity check passed.")

    print("\nSchedule for the 15-bed scenario:")
    for item in sorted(
        result["schedule"],
        key=lambda entry: (entry["room"], entry["start"]),
    ):
        print(
            f"{item['room']} | {item['surgery_id']} | "
            f"{item['start']}-{item['end']} | "
            f"Recovery: {item['recovery_start']}-"
            f"{item['recovery_end']} | "
            f"Beds: {item['recovery_beds']}"
        )

    print("\nAll recovery, room and staff checks passed.")


if __name__ == "__main__":
    main()

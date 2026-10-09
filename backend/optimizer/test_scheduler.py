
from data.demo_data import create_demo_data
from optimizer.scheduler import optimize_schedule


def main():
    data = create_demo_data()

    surgeries = data["surgeries"]
    operating_rooms = data["operating_rooms"]
    equipment = data["equipment"]
    staff = data["staff"]

    # Test OR-2 maintenance from 10:00 AM to 12:00 PM.
    or2 = next(
        room for room in operating_rooms if room.id == "OR-2"
    )
    or2.unavailable_periods = [
        {"start": 120, "end": 240}
    ]

    # Test a restricted surgeon shift.
    # Dr. Patel is available only from minute 60 to minute 300.
    surgeon = next(
        member for member in staff if member.id == "Dr. Patel"
    )
    surgeon.available_start = 60
    surgeon.available_end = 300

    result = optimize_schedule(
        surgeries,
        operating_rooms,
        equipment,
        staff,
    )

    print("\n==============================")
    print("SURGIPLAN CONSTRAINT TEST")
    print("==============================")
    print("Solver status:", result["status"])
    print("Scheduled:", len(result["schedule"]))
    print("Unscheduled:", len(result["unscheduled_surgeries"]))

    assert result["status"] in ("OPTIMAL", "FEASIBLE"), (
        "The optimizer did not find a valid solution."
    )

    rooms_by_id = {
        room.id: room for room in operating_rooms
    }
    staff_by_id = {
        member.id: member for member in staff
    }

    # Validate room availability, maintenance and staff working hours.
    for item in result["schedule"]:
        room = rooms_by_id[item["room"]]
        start = item["start"]
        end = item["end"]

        assert start >= room.available_start
        assert end <= room.available_end

        for period in room.unavailable_periods:
            overlaps = (
                start < period["end"]
                and end > period["start"]
            )
            assert not overlaps, (
                f"{item['surgery_id']} overlaps maintenance "
                f"in {room.id}."
            )

        for staff_id in (item["surgeon"], item["anesthetist"]):
            member = staff_by_id[staff_id]

            assert start >= member.available_start, (
                f"{staff_id} is unavailable when "
                f"{item['surgery_id']} starts."
            )
            assert end <= member.available_end, (
                f"{staff_id} is unavailable when "
                f"{item['surgery_id']} finishes."
            )

    # Validate that surgeries do not overlap within each OR.
    for room in operating_rooms:
        room_schedule = sorted(
            [
                item for item in result["schedule"]
                if item["room"] == room.id
            ],
            key=lambda item: item["start"],
        )

        for previous, current in zip(
            room_schedule, room_schedule[1:]
        ):
            assert previous["end"] <= current["start"], (
                f"Overlapping surgeries in {room.id}."
            )

    # Validate that each surgeon and anesthetist has no overlapping cases.
    for staff_field in ("surgeon", "anesthetist"):
        staff_schedule = {}

        for item in result["schedule"]:
            staff_id = item[staff_field]
            staff_schedule.setdefault(staff_id, []).append(item)

        for staff_id, items in staff_schedule.items():
            items.sort(key=lambda item: item["start"])

            for previous, current in zip(items, items[1:]):
                assert previous["end"] <= current["start"], (
                    f"{staff_id} has overlapping surgeries."
                )

    print("\nAll room, maintenance and staff checks passed.")

    print("\nSchedule:")
    for item in sorted(
        result["schedule"],
        key=lambda entry: (entry["room"], entry["start"]),
    ):
        print(
            f"{item['room']} | {item['surgery_id']} | "
            f"{item['start']}-{item['end']} | "
            f"{item['priority']} | Surgeon: {item['surgeon']}"
        )

    print("\nUnscheduled surgeries:")
    print(result["unscheduled_surgeries"])


if __name__ == "__main__":
    main()

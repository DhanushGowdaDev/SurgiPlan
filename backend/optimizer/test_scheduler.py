
from data.demo_data import create_demo_data
from optimizer.scheduler import optimize_schedule


def main():
    data = create_demo_data()

    surgeries = data["surgeries"]
    operating_rooms = data["operating_rooms"]
    equipment = data["equipment"]

    # Test maintenance in OR-2 from 10:00 AM to 12:00 PM.
    or2 = next(
        room for room in operating_rooms if room.id == "OR-2"
    )
    or2.unavailable_periods = [
        {"start": 120, "end": 240}
    ]

    result = optimize_schedule(
        surgeries,
        operating_rooms,
        equipment,
    )

    print("\n==============================")
    print("SURGIPLAN OR AVAILABILITY TEST")
    print("==============================")
    print("Solver status:", result["status"])
    print("Scheduled:", len(result["schedule"]))
    print("Unscheduled:", len(result["unscheduled_surgeries"]))

    if result["status"] not in ("OPTIMAL", "FEASIBLE"):
        raise AssertionError("The optimizer did not find a valid solution.")

    # Validate room working hours and maintenance.
    rooms_by_id = {
        room.id: room for room in operating_rooms
    }

    for item in result["schedule"]:
        room = rooms_by_id[item["room"]]
        start = item["start"]
        end = item["end"]

        assert start >= room.available_start, (
            f"{item['surgery_id']} starts before {room.id} opens."
        )
        assert end <= room.available_end, (
            f"{item['surgery_id']} finishes after {room.id} closes."
        )

        for period in room.unavailable_periods:
            overlaps = (
                start < period["end"]
                and end > period["start"]
            )
            assert not overlaps, (
                f"{item['surgery_id']} overlaps maintenance "
                f"in {room.id}: {start}-{end}"
            )

    # Validate that surgeries do not overlap within the same OR.
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
                f"Overlapping surgeries in {room.id}"
            )

    print("\nMaintenance and room availability checks passed.")
    print("\nSchedule:")

    for item in sorted(
        result["schedule"],
        key=lambda entry: (entry["room"], entry["start"]),
    ):
        print(
            f"{item['room']} | {item['surgery_id']} | "
            f"{item['start']}-{item['end']} | "
            f"{item['priority']}"
        )

    print("\nUnscheduled surgeries:")
    print(result["unscheduled_surgeries"])


if __name__ == "__main__":
    main()

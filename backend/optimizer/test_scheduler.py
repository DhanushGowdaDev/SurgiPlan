
from data.demo_data import create_demo_data
from optimizer.scheduler import optimize_schedule


def main():
    data = create_demo_data()

    surgeries = data["surgeries"]
    operating_rooms = data["operating_rooms"]
    equipment = data["equipment"]

    result = optimize_schedule(
        surgeries,
        operating_rooms,
        equipment,
    )

    print()
    print("==============================")
    print("SURGIPLAN OPTIMIZATION RESULT")
    print("==============================")
    print()

    print("Solver status:")
    print(result["status"])

    print()
    print("Scheduled surgeries:")
    print(len(result["schedule"]))

    print()
    print("Unscheduled surgeries:")
    print(len(result["unscheduled_surgeries"]))

    print()
    print("Schedule:")
    print()

    for item in sorted(
        result["schedule"],
        key=lambda row: (row["room"], row["start"]),
    ):
        equipment_text = ", ".join(
            item["required_equipment"]
        ) or "None"

        print(
            f'{item["room"]} | '
            f'{item["surgery_id"]} | '
            f'{item["procedure"]} | '
            f'{item["start"]}-{item["end"]} | '
            f'{item["priority"]} | '
            f'Equipment: {equipment_text}'
        )

    print()
    print("Unscheduled:")
    print(result["unscheduled_surgeries"])
    print()


if __name__ == "__main__":
    main()

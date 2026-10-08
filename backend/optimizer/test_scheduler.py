from data.demo_data import create_demo_data
from optimizer.scheduler import optimize_schedule


def main():
    data = create_demo_data()

    surgeries = data["surgeries"]
    operating_rooms = data["operating_rooms"]

    result = optimize_schedule(
        surgeries,
        operating_rooms
    )

    print("\n==============================")
    print("SURGIPLAN OPTIMIZATION RESULT")
    print("==============================\n")

    print("Solver status:")
    print(result["status"])

    print("\nScheduled surgeries:")
    print(len(result["schedule"]))

    print("\nUnscheduled surgeries:")
    print(len(result["unscheduled_surgeries"]))

    print("\nSchedule:\n")

    for item in sorted(
        result["schedule"],
        key=lambda x: (x["room"], x["start"])
    ):
        print(
            f'{item["room"]} | '
            f'{item["surgery_id"]} | '
            f'{item["procedure"]} | '
            f'{item["start"]}-{item["end"]} | '
            f'{item["priority"]}'
        )

    print("\nUnscheduled:")
    print(result["unscheduled_surgeries"])


if __name__ == "__main__":
    main()
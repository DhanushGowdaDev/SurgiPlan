
from dataclasses import asdict

from database import db, client
from data.demo_data import create_demo_data


COLLECTIONS = {
    "surgeries": "surgeries",
    "operating_rooms": "operating_rooms",
    "staff": "staff",
    "equipment": "equipment",
    "recovery_beds": "recovery_beds",
}


def seed_database():
    demo_data = create_demo_data()

    try:
        client.admin.command("ping")
        print(f"Connected to MongoDB database: {db.name}")

        for data_key, collection_name in COLLECTIONS.items():
            collection = db[collection_name]
            records = demo_data[data_key]

            for record in records:
                document = asdict(record)
                document["_id"] = document["id"]

                collection.replace_one(
                    {"_id": document["_id"]},
                    document,
                    upsert=True,
                )

            print(
                f"{collection_name}: "
                f"{collection.count_documents({})} records stored"
            )

        print("\nDemo data seeded successfully!")

    except Exception as exc:
        print(f"Database seeding failed: {exc}")
        raise


if __name__ == "__main__":
    seed_database()

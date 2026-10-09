
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise RuntimeError(
        "MONGODB_URI is missing. Check backend/.env."
    )

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=10000,
)

db = client["surgiplan"]


def check_database_connection():
    """Check whether MongoDB Atlas is reachable."""
    try:
        client.admin.command("ping")
        return {
            "connected": True,
            "database": db.name,
        }
    except PyMongoError as exc:
        return {
            "connected": False,
            "error": str(exc),
        }

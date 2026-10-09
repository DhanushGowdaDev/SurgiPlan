
import os
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from pydantic import BaseModel
from pymongo.errors import PyMongoError

from database import check_database_connection, db
from data.models import (
    Surgery,
    OperatingRoom,
    Staff,
    Equipment,
    RecoveryBed,
)
from optimizer.scheduler import optimize_schedule


load_dotenv()

app = FastAPI(
    title="SurgiPlan API",
    description="AI-Powered Operating Room Scheduling & Resource Optimization",
    version="0.1.0",
)


class CopilotRequest(BaseModel):
    message: str


def load_documents(collection_name):
    """Load MongoDB records without exposing MongoDB's internal _id."""
    documents = list(db[collection_name].find({}))

    for document in documents:
        document.pop("_id", None)

    return documents


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SurgiPlan API",
        "version": "0.1.0",
    }


@app.get("/api/health/database")
def database_health_check():
    result = check_database_connection()

    if not result["connected"]:
        raise HTTPException(
            status_code=503,
            detail="MongoDB connection failed.",
        )

    return {
        "status": "healthy",
        "database": result,
    }


@app.get("/api/surgeries")
def get_surgeries():
    try:
        return load_documents("surgeries")
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Unable to load surgeries from MongoDB.",
        )


@app.get("/api/operating-rooms")
def get_operating_rooms():
    try:
        return load_documents("operating_rooms")
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Unable to load operating rooms from MongoDB.",
        )


@app.get("/api/resources")
def get_resources():
    try:
        return {
            "staff": load_documents("staff"),
            "equipment": load_documents("equipment"),
            "recovery_beds": load_documents("recovery_beds"),
        }
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Unable to load resources from MongoDB.",
        )


@app.post("/api/schedule/optimize")
def run_schedule_optimization():
    try:
        surgery_data = load_documents("surgeries")
        room_data = load_documents("operating_rooms")
        staff_data = load_documents("staff")
        equipment_data = load_documents("equipment")
        bed_data = load_documents("recovery_beds")

        if not surgery_data or not room_data:
            raise HTTPException(
                status_code=400,
                detail="No surgeries or operating rooms found. Seed the database first.",
            )

        surgeries = [Surgery(**item) for item in surgery_data]
        rooms = [OperatingRoom(**item) for item in room_data]
        staff = [Staff(**item) for item in staff_data]
        equipment = [Equipment(**item) for item in equipment_data]
        recovery_beds = [RecoveryBed(**item) for item in bed_data]

        result = optimize_schedule(
            surgeries=surgeries,
            operating_rooms=rooms,
            equipment=equipment,
            staff=staff,
            recovery_beds=recovery_beds,
        )

        run_id = str(uuid4())

        run_document = {
            "_id": run_id,
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **result,
        }

        # Save the result and a history record.
        db.schedules.insert_one(run_document.copy())
        db.optimization_runs.insert_one(run_document.copy())

        return {
            "run_id": run_id,
            **result,
        }

    except HTTPException:
        raise
    except (TypeError, ValueError) as exc:
        print(f"Invalid scheduling data: {exc}")
        raise HTTPException(
            status_code=400,
            detail="Scheduling data is invalid. Check the stored records and backend logs.",
        )
    except PyMongoError as exc:
        print(f"MongoDB error: {exc}")
        raise HTTPException(
            status_code=503,
            detail="Database operation failed. Check MongoDB connectivity.",
        )
    except Exception as exc:
        print(f"Scheduling optimization failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Scheduling optimization failed. Check backend logs.",
        )


@app.get("/api/optimization-history")
def get_optimization_history():
    try:
        return list(
            db.optimization_runs.find(
                {},
                {"_id": 0},
            ).sort("created_at", -1).limit(20)
        )
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Unable to load optimization history.",
        )


@app.post("/api/copilot")
def copilot(request: CopilotRequest):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Gemma API key is not configured.",
        )

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="models/gemma-4-26b-a4b-it",
            contents=(
                "You are SurgiPlan Copilot, an assistant for operating-room "
                "scheduling. Explain scheduling concepts clearly. Do not "
                "invent schedule data, claim to have run the optimizer, or "
                "make medical decisions. No live schedule data is supplied "
                "to this endpoint yet.\n\n"
                f"User request: {request.message}"
            ),
        )

        return {
            "reply": response.text or "Gemma returned an empty response."
        }

    except Exception as exc:
        print(f"Gemma API error: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Gemma request failed. Check the backend terminal.",
        )

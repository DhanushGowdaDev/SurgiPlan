
import os
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from pydantic import BaseModel, Field
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://surgiplan-frontend.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CopilotRequest(BaseModel):
    message: str

class SimulationRequest(BaseModel):
    scenario_type: str
    target_id: str   

    procedure: str
    specialty: str
    duration: int
    surgeon: str
    anesthetist: str
    required_equipment: list[str] = []
    recovery_beds: int = 1
    recovery_duration: int = 60    


class EmergencyRequest(BaseModel):
    procedure: str = Field(min_length=1)
    specialty: str = Field(min_length=1)
    duration: int = Field(gt=0)
    surgeon: str = Field(min_length=1)
    anesthetist: str = Field(min_length=1)
    required_equipment: list[str] = Field(default_factory=list)
    recovery_beds: int = Field(ge=0)
    recovery_duration: int = Field(gt=0)

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

@app.post("/api/emergency")
def add_emergency_surgery(request: EmergencyRequest):
    try:
        surgery_data = load_documents("surgeries")
        room_data = load_documents("operating_rooms")
        staff_data = load_documents("staff")
        equipment_data = load_documents("equipment")
        bed_data = load_documents("recovery_beds")

        if not room_data:
            raise HTTPException(
                status_code=400,
                detail="No operating rooms found. Seed the database first.",
            )

        emergency_id = f"EMG-{uuid4().hex[:8].upper()}"

        emergency_document = {
    "id": emergency_id,
    "procedure": request.procedure.strip(),
    "specialty": request.specialty.strip(),
    "priority": "Emergency",
    "duration": request.duration,
    "surgeon": request.surgeon.strip(),
    "anesthetist": request.anesthetist.strip(),
    "required_equipment": request.required_equipment,
    "recovery_beds": request.recovery_beds,
    "recovery_duration": request.recovery_duration,
}
               # Validate required text fields.
        required_fields = [
            "procedure",
            "specialty",
            "surgeon",
            "anesthetist",
        ]

        for field_name in required_fields:
            if not emergency_document[field_name]:
                raise HTTPException(
                    status_code=422,
                    detail=f"{field_name.capitalize()} cannot be blank.",
                )

        # Validate that the requested staff members exist
        # and have the correct roles.
        staff_by_id = {
            member.id: member
            for member in [Staff(**item) for item in staff_data]
        }

        surgeon = staff_by_id.get(emergency_document["surgeon"])
        anesthetist = staff_by_id.get(emergency_document["anesthetist"])

        if surgeon is None or surgeon.role != "surgeon":
            raise HTTPException(
                status_code=422,
                detail="Selected surgeon does not exist or has an invalid role.",
            )

        if anesthetist is None or anesthetist.role != "anesthetist":
            raise HTTPException(
                status_code=422,
                detail="Selected anesthetist does not exist or has an invalid role.",
            )

               # Validate compatible operating-room specialty.
        compatible_rooms = [
            room
            for room in room_data
            if emergency_document["specialty"]
            in room.get("specialties", [])
        ]

        if not compatible_rooms:
            raise HTTPException(
                status_code=422,
                detail="No operating room supports this specialty.",
            )

        # Validate required equipment.
        available_equipment = {
            item["equipment_type"]
            for item in equipment_data
        }

        missing_equipment = [
            item
            for item in emergency_document["required_equipment"]
            if item not in available_equipment
        ]

        if missing_equipment:
            raise HTTPException(
                status_code=422,
                detail=f"Unavailable equipment: {', '.join(missing_equipment)}",
            )

                # Convert database records into model objects.
        existing_surgeries = [
            Surgery(**item) for item in surgery_data
        ]

        rooms = [
            OperatingRoom(**item) for item in room_data
        ]

        staff = [
            Staff(**item) for item in staff_data
        ]

        equipment = [
            Equipment(**item) for item in equipment_data
        ]

        recovery_beds = [
            RecoveryBed(**item) for item in bed_data
        ]

        # Calculate the schedule before adding the emergency.
        baseline = optimize_schedule(
            surgeries=existing_surgeries,
            operating_rooms=rooms,
            equipment=equipment,
            staff=staff,
            recovery_beds=recovery_beds,
        )

        # Add the emergency surgery to the existing queue.
        emergency_surgery = Surgery(**emergency_document)

        all_surgeries = existing_surgeries + [
            emergency_surgery
        ]

        # Re-optimize the schedule with emergency priority.
        result = optimize_schedule(
            surgeries=all_surgeries,
            operating_rooms=rooms,
            equipment=equipment,
            staff=staff,
            recovery_beds=recovery_beds,
        )

        # Check whether the emergency was actually scheduled.
        emergency_is_scheduled = any(
            item["surgery_id"] == emergency_document["id"]
            for item in result["schedule"]
        )

        if not emergency_is_scheduled:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Emergency could not be scheduled with the "
                    "currently available resources."
                ),
            )

        before = {
            item["surgery_id"]: item
            for item in baseline["schedule"]
        }
        after = {
            item["surgery_id"]: item
            for item in result["schedule"]
        }

        moved_surgeries = sorted(
            surgery_id
            for surgery_id in before.keys() & after.keys()
            if any(
                before[surgery_id][field] != after[surgery_id][field]
                for field in ("room", "start", "end")
            )
        )

        newly_unscheduled = sorted(before.keys() - after.keys())

        run_id = str(uuid4())

        run_document = {
            "_id": run_id,
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "event_type": "emergency_reoptimization",
            "emergency_surgery_id": emergency_id,
            **result,
        }

        db.surgeries.insert_one(emergency_document.copy())
        db.schedules.insert_one(run_document.copy())
        db.optimization_runs.insert_one(run_document.copy())

        return {
            "message": "Emergency surgery added and schedule re-optimized.",
            "emergency_surgery_id": emergency_id,
            "priority": "Emergency",
            "run_id": run_id,
            "status": result["status"],
            "schedule": result["schedule"],
            "unscheduled_surgeries": result["unscheduled_surgeries"],
            "comparison": {
                "previously_scheduled": len(before),
                "now_scheduled": len(after),
                "moved_surgeries": moved_surgeries,
                "newly_unscheduled": newly_unscheduled,
            },
            "saved_to_database": True,
        }

    except HTTPException:
        raise
    except (TypeError, ValueError) as exc:
        print(f"Invalid emergency scheduling data: {exc}")
        raise HTTPException(
            status_code=400,
            detail="Invalid scheduling data. Check the backend logs.",
        )
    except PyMongoError as exc:
        print(f"Emergency MongoDB error: {exc}")
        raise HTTPException(
            status_code=503,
            detail="Database operation failed. Check MongoDB connectivity.",
        )
    except Exception as exc:
        print(f"Emergency scheduling failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Emergency scheduling failed. Check backend logs.",
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

@app.post("/api/schedule/simulate")
def simulate_schedule(request: SimulationRequest):
    try:
        if request.scenario_type != "room_unavailable":
            raise HTTPException(
                status_code=400,
                detail="Supported scenario: room_unavailable",
            )

        # Load the current data from MongoDB.
        surgeries = [
            Surgery(**item)
            for item in load_documents("surgeries")
        ]
        rooms = [
            OperatingRoom(**item)
            for item in load_documents("operating_rooms")
        ]
        staff = [
            Staff(**item)
            for item in load_documents("staff")
        ]
        equipment = [
            Equipment(**item)
            for item in load_documents("equipment")
        ]
        recovery_beds = [
            RecoveryBed(**item)
            for item in load_documents("recovery_beds")
        ]

        # Verify the selected room exists.
        if not any(room.id == request.target_id for room in rooms):
            raise HTTPException(
                status_code=404,
                detail=f"Operating room '{request.target_id}' not found.",
            )

        # Original schedule: all rooms available.
        baseline = optimize_schedule(
            surgeries=surgeries,
            operating_rooms=rooms,
            equipment=equipment,
            staff=staff,
            recovery_beds=recovery_beds,
        )

        # Simulated schedule: remove the selected room.
        simulated_rooms = [
            room for room in rooms
            if room.id != request.target_id
        ]

        simulated = optimize_schedule(
            surgeries=surgeries,
            operating_rooms=simulated_rooms,
            equipment=equipment,
            staff=staff,
            recovery_beds=recovery_beds,
        )

        baseline_items = {
            item["surgery_id"]: item
            for item in baseline["schedule"]
        }
        simulated_items = {
            item["surgery_id"]: item
            for item in simulated["schedule"]
        }

        # Find surgeries whose room or scheduled time changed.
        moved = sorted(
            surgery_id
            for surgery_id in baseline_items.keys()
            & simulated_items.keys()
            if any(
                baseline_items[surgery_id][field]
                != simulated_items[surgery_id][field]
                for field in ("room", "start", "end")
            )
        )

        # Find surgeries that were scheduled before but not now.
        newly_unscheduled = sorted(
            baseline_items.keys() - simulated_items.keys()
        )

        return {
            "scenario": {
                "type": request.scenario_type,
                "target_id": request.target_id,
            },
            "baseline": baseline,
            "simulated": simulated,
            "comparison": {
                "baseline_scheduled": len(baseline_items),
                "simulated_scheduled": len(simulated_items),
                "baseline_unscheduled": len(
                    baseline["unscheduled_surgeries"]
                ),
                "simulated_unscheduled": len(
                    simulated["unscheduled_surgeries"]
                ),
                "moved_surgeries": moved,
                "newly_unscheduled": newly_unscheduled,
            },
            "saved_to_database": False,
        }

    except HTTPException:
        raise
    except (TypeError, ValueError) as exc:
        print(f"Invalid simulation data: {exc}")
        raise HTTPException(
            status_code=400,
            detail="Invalid scheduling data. Check the backend logs.",
        )
    except PyMongoError as exc:
        print(f"MongoDB simulation error: {exc}")
        raise HTTPException(
            status_code=503,
            detail="Unable to load simulation data from MongoDB.",
        )
    except Exception as exc:
        print(f"Simulation failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Simulation failed. Check the backend logs.",
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

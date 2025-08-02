from fastapi import FastAPI, HTTPException, Depends, Header
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import the updated generate_optimal_schedule function
from scripts.dumb_scheduler import generate_dumb_schedule
from scripts.optimal_scheduler import generate_optimal_schedule

# Import portfolio authentication
from portfolio_auth import verify_portfolio_auth

# Import database utilities
from database import SchedulerDatabase


app = FastAPI()

# Initialize database instance
database = SchedulerDatabase()

# Get API secret key from environment
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
SCHEDULER_ADMIN_PASSWORD = os.getenv("SCHEDULER_ADMIN_PASSWORD")

# Define allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:4321",  # Portfolio dev server
    "http://127.0.0.1:4321",  # Alternative local
    "https://kylesimons.ca",  # Production portfolio domain
    "https://www.kylesimons.ca",  # Include www subdomain
    "https://kksimons-portfolio-2025-36.deno.dev",  # Deno deploy stable URL
]


class SingleOriginCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        origin = request.headers.get("origin")
        print(f"🔧 CORS Middleware: Processing request from origin: {origin}")

        # Handle preflight requests
        if request.method == "OPTIONS":
            print(f"🔧 CORS Middleware: Handling OPTIONS preflight request")
            if origin in ALLOWED_ORIGINS:
                print(f"🔧 CORS Middleware: Origin {origin} is allowed")
                response = Response()
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, OPTIONS, PUT, DELETE"
                )
                response.headers["Access-Control-Allow-Headers"] = "*"
                response.headers["Access-Control-Allow-Credentials"] = "false"
                return response
            else:
                print(f"🔧 CORS Middleware: Origin {origin} is NOT allowed")

        response = await call_next(request)

        # Only add CORS headers if origin is allowed
        if origin in ALLOWED_ORIGINS:
            print(f"🔧 CORS Middleware: Adding CORS headers for origin: {origin}")
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, OPTIONS, PUT, DELETE"
            )
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "false"
        else:
            print(f"🔧 CORS Middleware: NOT adding CORS headers for origin: {origin}")

        return response


# Add our custom CORS middleware
app.add_middleware(SingleOriginCORSMiddleware)


def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


def verify_admin_auth(
    portfolio_key: str = Depends(verify_portfolio_auth),
    x_admin_password: str = Header(None),
):
    """
    Verify both portfolio authentication and admin password
    """
    if not x_admin_password:
        raise HTTPException(
            status_code=401, detail="Missing admin password header (X-Admin-Password)"
        )

    if not SCHEDULER_ADMIN_PASSWORD:
        raise HTTPException(
            status_code=500, detail="Admin password not configured on server"
        )

    if x_admin_password != SCHEDULER_ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    return {"portfolio_key": portfolio_key, "admin_authenticated": True}


# Define Pydantic models for data validation and parsing
class DayInfo(BaseModel):
    day: str  # Day of the week (e.g., "M", "Tu")
    start: str  # Start time in "HH:MM" format
    end: str  # End time in "HH:MM" format
    format: str  # Class format ("online" or "in-person")


class Section(BaseModel):
    day1: DayInfo  # First day information
    day2: DayInfo  # Second day information
    professor: str  # Professor's name


class Course(BaseModel):
    course: str  # Course name or code
    sections: List[Section]  # List of available sections for the course


class ClassScheduleInput(BaseModel):
    courses: List[Course]  # List of courses to schedule
    exclude_weekend: Optional[bool] = (
        True  # Option to exclude weekends, default to exclude (true)
    )


@app.get("/")
def read_root():
    """
    Root endpoint to confirm the API is running.
    """
    return {
        "message": "Class Scheduler is up!",
        "version": "2024-08-01-v2",
        "cors_middleware": "SingleOriginCORSMiddleware",
    }


@app.post("/api/v1/class-scheduler")
async def class_scheduler(
    data: ClassScheduleInput, api_key: str = Depends(verify_api_key)
):
    """
    API endpoint to generate the optimal class schedule.
    Args:
        data (ClassScheduleInput): Input data in json containing courses and options.
    Returns:
        dict: A response containing the optimal schedule or an error message.
    """
    # Extract courses and exclude_weekend option from the input data
    course_data = data.courses
    exclude_weekend = data.exclude_weekend

    # Convert the Pydantic models to dictionaries for processing
    courses = [course.dict() for course in course_data]

    # Generate the optimal schedule using the provided courses data
    optimal_schedule, best_score = generate_dumb_schedule(
        courses, exclude_weekend=exclude_weekend
    )

    if optimal_schedule:
        response = {
            "result": (
                f"Optimal Schedule (Weekday days off: {best_score[0]}, "
                f"Online-only days: {best_score[1]})"
            ),
            "schedules": optimal_schedule,
        }
    else:
        response = {"message": "No valid schedule found within the time limit."}

    return response


# this is for the optimal scheduler
@app.post("/api/v1/class-scheduler-optimal")
async def class_scheduler_optimal(
    data: ClassScheduleInput, api_key: str = Depends(verify_api_key)
):
    """
    API endpoint to generate the optimal class schedule using the optimal scheduler.
    """

    # Convert the Pydantic models to dictionaries for processing
    courses = [course.dict() for course in data.courses]
    exclude_weekend = data.exclude_weekend

    # Generate the optimal schedule using the optimal scheduler
    optimal_schedule, best_score = generate_optimal_schedule(
        courses, exclude_weekend=exclude_weekend
    )

    if optimal_schedule:
        response = {
            "result": (
                f"Optimal Schedule (Weekday days off: {best_score[0]}, "
                f"Online-only days: {best_score[1]})"
            ),
            "schedules": optimal_schedule,
        }
    else:
        response = {"message": "No valid schedule found within the time limit."}

    return response


# New Portfolio-specific endpoints
class PortfolioScheduleRequest(BaseModel):
    courses: List[Course]
    preferences: Optional[dict] = {}


class PortfolioOptimalRequest(BaseModel):
    courses: List[Course]
    count: Optional[int] = 5
    preferences: Optional[dict] = {}


class PortfolioValidateRequest(BaseModel):
    schedule: List[dict]  # List of selected course sections


class ShareScheduleRequest(BaseModel):
    schedule: List[dict]  # Schedule data to share
    metadata: Optional[dict] = {}  # Additional metadata (program, term, etc.)
    alias: Optional[str] = None  # Custom alias for shorter URLs


# Dataset management models
class DatasetRequest(BaseModel):
    action: str  # "create" or "update"
    dataset: dict
    datasetId: Optional[str] = None


@app.post("/api/generate-schedule")
async def portfolio_generate_schedule(
    data: PortfolioScheduleRequest, portfolio_key: str = Depends(verify_portfolio_auth)
):
    """
    Portfolio endpoint to generate a schedule
    """
    print(f"📱 Portfolio request authenticated with key: {portfolio_key[:8]}...")

    # Convert to the format expected by existing schedulers
    courses = [course.dict() for course in data.courses]
    exclude_weekend = data.preferences.get("exclude_weekend", True)

    # Use the dumb scheduler for basic generation
    optimal_schedule, best_score = generate_dumb_schedule(
        courses, exclude_weekend=exclude_weekend
    )

    if optimal_schedule:
        # Convert to portfolio format
        schedule_selections = []
        for section_data in optimal_schedule:
            schedule_selections.append(
                {
                    "course": section_data.get("course", "Unknown"),
                    "professor": section_data.get("professor", "Unknown"),
                    "section": section_data,
                }
            )

        return {
            "schedule": schedule_selections,
            "message": "Schedule generated successfully",
            "score": best_score,
        }
    else:
        return {"schedule": [], "message": "No valid schedule found"}


@app.post("/api/optimal-schedules")
async def portfolio_optimal_schedules(
    data: PortfolioOptimalRequest, portfolio_key: str = Depends(verify_portfolio_auth)
):
    """
    Portfolio endpoint to get multiple optimal schedules
    """
    print(
        f"📱 Portfolio optimal schedules request authenticated with key: {portfolio_key[:8]}..."
    )

    courses = [course.dict() for course in data.courses]
    requested_count = data.count or 5
    user_exclude_weekend = data.preferences.get("exclude_weekend", True)

    print(
        f"📅 User preferences: exclude_weekend={user_exclude_weekend}, requested_count={requested_count}"
    )

    schedules = []

    # Generate multiple schedule variations by trying different approaches
    # Create more diverse variations by using different strategies
    variation_configs = [
        {
            "exclude_weekend": user_exclude_weekend,
            "time_limit": 30,
            "strategy": "optimal",
        },  # Primary optimal solution
        {
            "exclude_weekend": user_exclude_weekend,
            "time_limit": 15,
            "strategy": "dumb",
        },  # Fast alternative using dumb scheduler
        {
            "exclude_weekend": user_exclude_weekend,
            "time_limit": 25,
            "strategy": "optimal",
        },  # Secondary optimal with different timeout
        {
            "exclude_weekend": user_exclude_weekend,
            "time_limit": 8,
            "strategy": "dumb",
        },  # Quick dumb scheduler variation
        {
            "exclude_weekend": user_exclude_weekend,
            "time_limit": 12,
            "strategy": "dumb",
        },  # Medium dumb scheduler variation
    ]

    generated_schedules = set()  # Track unique schedules to avoid duplicates

    for i, config in enumerate(variation_configs[:requested_count]):
        try:
            print(f"🔄 Generating variation {i + 1} with config: {config}")

            # Use the specified strategy
            optimal_schedule = None
            best_score = None

            if config.get("strategy") == "optimal":
                # Try optimal scheduler first
                try:
                    optimal_schedule, best_score = generate_optimal_schedule(
                        courses, exclude_weekend=config["exclude_weekend"]
                    )
                    print(f"✅ Optimal scheduler succeeded for variation {i + 1}")
                except Exception as e:
                    print(f"❌ Optimal scheduler failed for variation {i + 1}: {e}")
                    optimal_schedule = None

            # Use dumb scheduler if strategy is "dumb" or if optimal failed
            if not optimal_schedule or config.get("strategy") == "dumb":
                try:
                    # Use randomization for dumb scheduler variations to get different results
                    use_randomization = (
                        i > 0
                    )  # First one uses normal order, rest are randomized
                    optimal_schedule, best_score = generate_dumb_schedule(
                        courses,
                        exclude_weekend=config["exclude_weekend"],
                        time_limit=config.get("time_limit", 30),
                        randomize=use_randomization,
                    )
                    print(
                        f"✅ Dumb scheduler succeeded for variation {i + 1} (randomized: {use_randomization})"
                    )
                except Exception as e:
                    print(f"❌ Dumb scheduler failed for variation {i + 1}: {e}")
                    optimal_schedule = None

            if optimal_schedule:
                # Create a comprehensive signature for this schedule to detect duplicates
                schedule_signature = []
                for section_data in optimal_schedule:
                    # Include course, professor, and time slots in signature
                    day1_sig = f"{section_data.get('day1', {}).get('day', '')}-{section_data.get('day1', {}).get('start', '')}"
                    day2_sig = f"{section_data.get('day2', {}).get('day', '')}-{section_data.get('day2', {}).get('start', '')}"
                    signature_part = f"{section_data.get('course', '')}-{section_data.get('professor', '')}-{day1_sig}-{day2_sig}"
                    schedule_signature.append(signature_part)
                schedule_signature = sorted(schedule_signature)
                signature_str = "|".join(schedule_signature)

                # Only add if it's unique
                if signature_str not in generated_schedules:
                    generated_schedules.add(signature_str)

                    # Convert to portfolio format
                    selections = []
                    for section_data in optimal_schedule:
                        selections.append(
                            {
                                "course": section_data.get("course", "Unknown"),
                                "professor": section_data.get("professor", "Unknown"),
                                "section": section_data,
                            }
                        )

                    # Calculate conflict score (basic implementation)
                    conflict_score = 0
                    time_slots = {}
                    for section_data in optimal_schedule:
                        for day_key in ["day1", "day2"]:
                            if day_key in section_data:
                                day_info = section_data[day_key]
                                time_key = f"{day_info.get('day')}-{day_info.get('start')}-{day_info.get('end')}"
                                if time_key in time_slots:
                                    conflict_score += 1
                                time_slots[time_key] = True

                    schedules.append(
                        {
                            "selections": selections,
                            "conflictScore": conflict_score,
                            "score": sum(best_score)
                            if isinstance(best_score, (list, tuple))
                            else best_score,
                            "variation": i + 1,
                            "config": config,
                        }
                    )

                    print(f"✅ Generated unique variation {i + 1}")
                else:
                    print(f"⚠️ Variation {i + 1} was duplicate, skipping")
            else:
                print(f"❌ Failed to generate variation {i + 1}")

        except Exception as e:
            print(f"❌ Error generating variation {i + 1}: {e}")
            continue

    # If we don't have enough unique schedules, pad with the best one we have
    if len(schedules) == 1 and requested_count > 1:
        base_schedule = schedules[0]
        for i in range(1, min(requested_count, 3)):  # Don't spam too many duplicates
            duplicate_schedule = base_schedule.copy()
            duplicate_schedule["variation"] = i + 1
            schedules.append(duplicate_schedule)

    return {
        "schedules": schedules,
        "message": f"Generated {len(schedules)} schedule variation(s)",
    }


@app.post("/api/validate-schedule")
async def portfolio_validate_schedule(
    data: PortfolioValidateRequest, portfolio_key: str = Depends(verify_portfolio_auth)
):
    """
    Portfolio endpoint to validate a schedule for conflicts
    """
    print(
        f"📱 Portfolio validation request authenticated with key: {portfolio_key[:8]}..."
    )

    # Simple conflict detection
    conflicts = []
    time_slots = {}

    for selection in data.schedule:
        section = selection.get("section", {})
        course = selection.get("course", "Unknown")

        # Check both day1 and day2 for conflicts
        for day_key in ["day1", "day2"]:
            if day_key in section:
                day_info = section[day_key]
                day = day_info.get("day")
                start = day_info.get("start")
                end = day_info.get("end")

                if day and start and end:
                    key = f"{day}-{start}-{end}"
                    if key in time_slots:
                        conflicts.append(
                            {
                                "course1": course,
                                "course2": time_slots[key],
                                "day": day,
                                "time": f"{start}-{end}",
                            }
                        )
                    else:
                        time_slots[key] = course

    return {
        "valid": len(conflicts) == 0,
        "conflicts": conflicts,
        "message": f"Validation complete. {len(conflicts)} conflicts found.",
    }


# Dataset Management Endpoints


@app.get("/api/datasets")
async def get_datasets(portfolio_key: str = Depends(verify_portfolio_auth)):
    """
    Portfolio endpoint to get available course datasets
    """
    print(
        f"📱 Portfolio datasets GET request authenticated with key: {portfolio_key[:8]}..."
    )

    try:
        datasets = await database.list_datasets()
        return {"success": True, "datasets": datasets}
    except Exception as e:
        print(f"❌ Failed to list datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/datasets")
async def manage_datasets(
    data: DatasetRequest, portfolio_key: str = Depends(verify_portfolio_auth)
):
    """
    Portfolio endpoint to create or update datasets
    """
    print(
        f"📱 Portfolio datasets POST request authenticated with key: {portfolio_key[:8]}..."
    )

    try:
        if data.action == "create":
            result = await database.save_dataset(data.dataset)
            return result
        elif data.action == "update" and data.datasetId:
            result = await database.update_dataset(data.datasetId, data.dataset)
            return result
        else:
            raise HTTPException(
                status_code=400, detail="Invalid action or missing datasetId for update"
            )
    except Exception as e:
        print(f"❌ Failed to manage dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: str, portfolio_key: str = Depends(verify_portfolio_auth)
):
    """
    Portfolio endpoint to get a specific dataset
    """
    print(
        f"📱 Portfolio dataset GET request authenticated with key: {portfolio_key[:8]}..."
    )

    try:
        dataset = await database.load_dataset(dataset_id)
        return {"success": True, "dataset": dataset}
    except Exception as e:
        print(f"❌ Failed to load dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str, portfolio_key: str = Depends(verify_portfolio_auth)
):
    """
    Portfolio endpoint to delete a specific dataset
    """
    print(
        f"📱 Portfolio dataset DELETE request authenticated with key: {portfolio_key[:8]}..."
    )

    try:
        result = await database.delete_dataset(dataset_id)
        return result
    except Exception as e:
        print(f"❌ Failed to delete dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/share-schedule")
async def share_schedule(
    data: ShareScheduleRequest, portfolio_key: str = Depends(verify_portfolio_auth)
):
    """
    Portfolio endpoint to share a schedule
    """
    print(
        f"📱 Portfolio share schedule request authenticated with key: {portfolio_key[:8]}..."
    )

    try:
        result = await database.save_shared_schedule(
            schedule_data=data.schedule,
            metadata=data.metadata,
            expires_in_days=30,  # Expire after 30 days
            alias=data.alias,
        )
        return result
    except Exception as e:
        print(f"❌ Failed to share schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/shared-schedule/{share_id}")
async def get_shared_schedule(share_id: str):
    """
    Public endpoint to get a shared schedule (no auth required)
    """
    print(f"📱 Getting shared schedule: {share_id}")

    try:
        result = await database.get_shared_schedule(share_id)
        if result is None:
            raise HTTPException(
                status_code=404, detail="Shared schedule not found or expired"
            )

        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to get shared schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin-only endpoints (require both portfolio auth + admin password)


class AdminDatasetRenameRequest(BaseModel):
    name: str


@app.put("/api/admin/datasets/{dataset_id}/rename")
async def admin_rename_dataset(
    dataset_id: str,
    data: AdminDatasetRenameRequest,
    auth: dict = Depends(verify_admin_auth),
):
    """
    Admin endpoint to rename a dataset
    """
    print(f"🔐 Admin rename dataset request for: {dataset_id}")

    try:
        # Ensure database is initialized
        if not database.is_initialized:
            await database.initialize_database()

        # First check if dataset exists
        await database.load_dataset(dataset_id)

        # Update the dataset name in the database
        from datetime import datetime

        now_iso = datetime.utcnow().isoformat()

        await database.client.execute(
            "UPDATE datasets SET name = ?, updated_at = ? WHERE id = ?",
            [data.name.strip()[:255], now_iso, dataset_id],
        )

        return {"success": True, "message": "Dataset renamed successfully"}

    except Exception as e:
        print(f"❌ Failed to rename dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/admin/datasets/{dataset_id}")
async def admin_delete_dataset(
    dataset_id: str, auth: dict = Depends(verify_admin_auth)
):
    """
    Admin endpoint to delete a dataset
    """
    print(f"🔐 Admin delete dataset request for: {dataset_id}")

    try:
        result = await database.delete_dataset(dataset_id)
        return result
    except Exception as e:
        print(f"❌ Failed to delete dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/datasets/{dataset_id}/links")
async def admin_get_dataset_links(
    dataset_id: str, auth: dict = Depends(verify_admin_auth)
):
    """
    Admin endpoint to get shareable links for a dataset
    """
    print(f"🔐 Admin get dataset links request for: {dataset_id}")

    try:
        # First verify dataset exists
        dataset = await database.load_dataset(dataset_id)

        # For now, just return the direct dataset link
        # In the future, you could add actual shareable link management
        base_url = "https://kylesimons.ca"  # Or get from environment
        direct_link = f"{base_url}/scheduler?dataset={dataset_id}"

        return {
            "success": True,
            "links": [
                {
                    "type": "dataset",
                    "url": direct_link,
                    "description": f"Direct link to {dataset['name']} dataset",
                }
            ],
        }

    except Exception as e:
        print(f"❌ Failed to get dataset links: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/shared-schedules")
async def admin_get_shared_schedules(auth: dict = Depends(verify_admin_auth)):
    """
    Admin endpoint to get all shared schedule links
    """
    print("🔐 Admin get shared schedules request")

    try:
        # Ensure database is initialized
        if not database.is_initialized:
            await database.initialize_database()

        # Get all shared schedules
        result = await database.client.execute("""
            SELECT id, alias, metadata, created_at, expires_at, view_count
            FROM shared_schedules 
            ORDER BY created_at DESC
        """)

        shared_schedules = []
        base_url = "https://kylesimons.ca"

        for row in result.rows:
            # Parse metadata for additional info
            metadata = {}
            if row["metadata"]:
                try:
                    metadata = json.loads(row["metadata"])
                except:
                    pass

            share_key = row["alias"] if row["alias"] else row["id"]
            share_url = f"{base_url}/scheduler?share={share_key}"

            # Check if expired
            is_expired = False
            if row["expires_at"]:
                try:
                    expires_at = datetime.fromisoformat(row["expires_at"])
                    is_expired = datetime.now() > expires_at
                except:
                    pass

            shared_schedules.append({
                "id": row["id"],
                "alias": row["alias"],
                "shareKey": share_key,
                "shareUrl": share_url,
                "metadata": metadata,
                "createdAt": row["created_at"],
                "expiresAt": row["expires_at"],
                "viewCount": row["view_count"] or 0,
                "isExpired": is_expired,
                "description": metadata.get("program", "Unknown") + " - " + metadata.get("term", "Unknown") if metadata else "Shared Schedule"
            })

        return {
            "success": True,
            "sharedSchedules": shared_schedules,
            "total": len(shared_schedules)
        }

    except Exception as e:
        print(f"❌ Failed to get shared schedules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/admin/shared-schedules/{share_id}")
async def admin_delete_shared_schedule(
    share_id: str, auth: dict = Depends(verify_admin_auth)
):
    """
    Admin endpoint to delete a shared schedule link
    """
    print(f"🔐 Admin delete shared schedule request for: {share_id}")

    try:
        # Ensure database is initialized
        if not database.is_initialized:
            await database.initialize_database()

        # Delete the shared schedule
        result = await database.client.execute(
            "DELETE FROM shared_schedules WHERE id = ? OR alias = ?",
            [share_id, share_id]
        )

        return {"success": True, "message": "Shared schedule deleted successfully"}

    except Exception as e:
        print(f"❌ Failed to delete shared schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the FastAPI application with uvicorn server
    uvicorn.run(app="app:app", host="0.0.0.0", port=8502, reload=True)

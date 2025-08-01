from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

# Import the updated generate_optimal_schedule function
from scripts.dumb_scheduler import generate_dumb_schedule
from scripts.optimal_scheduler import generate_optimal_schedule

# Import portfolio authentication
from portfolio_auth import verify_portfolio_auth


app = FastAPI()

# Get API secret key from environment
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

# Enable CORS for specific origins (portfolio domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:4321",  # Portfolio dev server
        "http://127.0.0.1:4321",  # Alternative local
        "https://kylesimons.ca",  # Production portfolio domain
        "https://www.kylesimons.ca",  # Include www subdomain
        "https://kksimons-portfolio-2025-36.deno.dev",  # Deno deploy stable URL
    ],
    allow_credentials=False,  # Portfolio auth doesn't use credentials
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
)


def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


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
    return {"message": "Class Scheduler is up!"}


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


class PortfolioValidateRequest(BaseModel):
    schedule: List[dict]  # List of selected course sections


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

    schedules = []

    # Generate multiple schedule variations by trying different approaches
    variation_configs = [
        {"exclude_weekend": True, "time_limit": 30},  # Optimal with full time
        {"exclude_weekend": True, "time_limit": 15},  # Faster search
        {"exclude_weekend": False, "time_limit": 20},  # Include weekends
        {"exclude_weekend": True, "time_limit": 10},  # Quick search
        {"exclude_weekend": False, "time_limit": 10},  # Quick with weekends
    ]

    generated_schedules = set()  # Track unique schedules to avoid duplicates

    for i, config in enumerate(variation_configs[:requested_count]):
        try:
            print(f"🔄 Generating variation {i + 1} with config: {config}")

            # Try optimal scheduler first
            try:
                optimal_schedule, best_score = generate_optimal_schedule(
                    courses, exclude_weekend=config["exclude_weekend"]
                )
            except Exception as e:
                print(f"Optimal scheduler failed: {e}")
                optimal_schedule = None

            # If optimal scheduler fails, fall back to dumb scheduler
            if not optimal_schedule:
                optimal_schedule, best_score = generate_dumb_schedule(
                    courses,
                    exclude_weekend=config["exclude_weekend"],
                    time_limit=config.get("time_limit", 30),
                )

            if optimal_schedule:
                # Create a signature for this schedule to detect duplicates
                schedule_signature = []
                for section_data in optimal_schedule:
                    signature_part = f"{section_data.get('course', '')}-{section_data.get('professor', '')}"
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


@app.get("/api/datasets")
async def get_datasets(portfolio_key: str = Depends(verify_portfolio_auth)):
    """
    Portfolio endpoint to get available course datasets
    """
    print(f"📱 Portfolio datasets request authenticated with key: {portfolio_key[:8]}...")
    
    # Return mock datasets for now - in production this would come from a database
    datasets = [
        {
            "id": "software-dev-winter-2024",
            "name": "Software Development - Winter 2024",
            "program": "Software Development",
            "term": "Winter 2024",
            "courses": [
                {
                    "course": "COMM 238",
                    "name": "Technical Communications I",
                    "sections": []
                },
                {
                    "course": "CPNT 217", 
                    "name": "Introduction to Network Systems",
                    "sections": []
                },
                {
                    "course": "CPRG 213",
                    "name": "Web Development 1", 
                    "sections": []
                },
                {
                    "course": "CPRG 216",
                    "name": "Object-Oriented Programming 1",
                    "sections": []
                }
            ]
        }
    ]
    
    return {"datasets": datasets}


if __name__ == "__main__":
    # Run the FastAPI application with uvicorn server
    uvicorn.run(app="app:app", host="0.0.0.0", port=8502, reload=True)

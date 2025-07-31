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
        "*",  # Allow all origins for development - remove in production
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
        for course_name, section_data in optimal_schedule.items():
            schedule_selections.append(
                {
                    "course": course_name,
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

    # Generate optimal schedule
    optimal_schedule, best_score = generate_optimal_schedule(
        courses, exclude_weekend=True
    )

    schedules = []
    if optimal_schedule:
        # Convert to portfolio format
        selections = []
        for course_name, section_data in optimal_schedule.items():
            selections.append(
                {
                    "course": course_name,
                    "professor": section_data.get("professor", "Unknown"),
                    "section": section_data,
                }
            )

        schedules.append(
            {
                "selections": selections,
                "conflictScore": 0,  # You can implement conflict detection
                "score": sum(best_score)
                if isinstance(best_score, (list, tuple))
                else best_score,
            }
        )

        # Generate a few variations if possible
        # For now, just return the one optimal schedule
        # You could enhance this to generate multiple different schedules

    return {
        "schedules": schedules,
        "message": f"Generated {len(schedules)} optimal schedule(s)",
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


if __name__ == "__main__":
    # Run the FastAPI application with uvicorn server
    uvicorn.run(app="app:app", host="0.0.0.0", port=8502, reload=True)

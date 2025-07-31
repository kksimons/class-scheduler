from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# Import the updated generate_optimal_schedule function
from scripts.dumb_scheduler import generate_dumb_schedule
from scripts.optimal_scheduler import generate_optimal_schedule


app = FastAPI()

# Enable CORS for all origins and methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


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
async def class_scheduler(data: ClassScheduleInput):
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
async def class_scheduler_optimal(data: ClassScheduleInput):
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


if __name__ == "__main__":
    # Run the FastAPI application with uvicorn server
    uvicorn.run(app="app:app", host="0.0.0.0", port=8502, reload=True)

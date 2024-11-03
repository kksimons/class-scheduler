from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from scripts.dp import generate_optimal_schedule

app = FastAPI()

# Enable CORS for all origins and methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DayInfo(BaseModel):
    day: str
    start: str
    end: str
    format: str

class Section(BaseModel):
    day1: DayInfo
    day2: DayInfo
    professor: str

class Course(BaseModel):
    course: str
    sections: List[Section]

class ClassScheduleInput(BaseModel):
    courses: List[Course]
    exclude_weekend: Optional[bool] = True  # Optional field to decide if weekends are excluded

@app.get("/")
def read_root():
    return {"message": "Class Scheduler is up!"}

@app.post("/api/v1/class-scheduler")
async def class_scheduler(data: ClassScheduleInput):
    # Extract courses and exclude_weekend option from the input data
    course_data = data.courses
    exclude_weekend = data.exclude_weekend

    # Generate the optimal schedule
    optimal_schedule, best_score = generate_optimal_schedule(
        [course.dict() for course in course_data], exclude_weekend=exclude_weekend
    )

    if optimal_schedule:
        response = {
            "result": f"Optimal Schedule (Weekday days off: {best_score[0]}, Online-only days: {best_score[1]})",
            "schedules": optimal_schedule
        }
    else:
        response = {"message": "No valid schedule found within the time limit."}

    return response

if __name__ == "__main__":
    uvicorn.run(app="app:app", host="0.0.0.0", port=8502, reload=True)

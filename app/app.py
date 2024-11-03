from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from scripts.scheduler import create_class_scheduling_model, solve_class_scheduling
import uvicorn
import json

app = FastAPI()

# For CORS
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

@app.get("/")
def read_root():
    return {"message": "Class Scheduler is up!"}

@app.post("/api/v1/class-scheduler")
async def class_scheduler(data: ClassScheduleInput, request: Request):
    # Log the incoming request body for debugging
    print("Received data:", json.dumps(data.dict(), indent=2))
    
    model, shifts = create_class_scheduling_model(data.courses)
    results = solve_class_scheduling(model, shifts, data.courses)
    
    # Log the response before sending it back to the client
    print("Generated schedule response:", json.dumps(results, indent=2))

    return {"schedules": results}

if __name__ == "__main__":
    uvicorn.run(app="app:app", host="0.0.0.0", port=8502, reload=True)

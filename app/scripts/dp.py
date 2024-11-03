import json
import itertools
import time
from pathlib import Path

def load_courses(filename="courseDefaults.json"):
    with open(filename, "r") as file:
        return json.load(file)

def parse_time(time_str):
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes

def mark_time(day_vector, start, end):
    for minute in range(start, end):
        day_vector[minute] = 1

def is_free(day_vector, start, end):
    return all(day_vector[minute] == 0 for minute in range(start, end))

def evaluate_schedule(schedule):
    weekdays = {"M", "Tu", "W", "Th", "F"}
    day_classes = {day: {"online": 0, "in-person": 0} for day in weekdays}
    
    for section in schedule:
        for day_key in ["day1", "day2"]:
            day_info = section.get(day_key)
            if day_info and day_info["day"] in weekdays:
                day_classes[day_info["day"]][day_info["format"]] += 1

    days_off = sum(1 for day, classes in day_classes.items() if all(v == 0 for v in classes.values()))
    online_only_days = sum(1 for day, classes in day_classes.items() if classes["in-person"] == 0 and classes["online"] > 0)
    
    return days_off, online_only_days

def generate_optimal_schedule(courses, time_limit=30, exclude_weekend=True):
    start_time = time.time()
    best_schedule = []
    best_score = (0, 0)

    valid_days = {"M", "Tu", "W", "Th", "F"}
    if not exclude_weekend:
        valid_days.add("S")

    for course_combination in itertools.product(*[course["sections"] for course in courses]):
        if time.time() - start_time > time_limit:
            break

        day_vectors = {day: [0] * (24 * 60) for day in valid_days}
        structured_schedule = []

        conflict_found = False
        for idx, section in enumerate(course_combination):
            course_name = courses[idx]["course"]
            professor = section["professor"]
            day1 = section["day1"]
            day2 = section["day2"]

            for day_info in [day1, day2]:
                if day_info["day"] in day_vectors:
                    start = parse_time(day_info["start"])
                    end = parse_time(day_info["end"])

                    if not is_free(day_vectors[day_info["day"]], start, end):
                        conflict_found = True
                        break
                    mark_time(day_vectors[day_info["day"]], start, end)

            if conflict_found:
                break

            structured_schedule.append({
                "course": course_name,
                "day1": day1,
                "day2": day2,
                "professor": professor
            })

        if conflict_found:
            continue

        days_off, online_only_days = evaluate_schedule(course_combination)

        if (days_off, online_only_days) > best_score:
            best_schedule = structured_schedule
            best_score = (days_off, online_only_days)

    return best_schedule, best_score if best_schedule else None

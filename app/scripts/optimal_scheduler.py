from ortools.sat.python import cp_model
from typing import List, Dict, Any, Tuple, Optional

def parse_time_to_minutes(time_str: str) -> int:
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes

def generate_optimal_schedule(courses: List[Dict[str, Any]], exclude_weekend: bool = True) -> Optional[Tuple[List[Dict[str, Any]], Tuple[int, int]]]:
    model = cp_model.CpModel()

    # Define valid days based on whether weekends are excluded
    valid_days = ["M", "Tu", "W", "Th", "F"]
    if not exclude_weekend:
        valid_days.extend(["S", "Su"])
    day_to_index = {day: idx for idx, day in enumerate(valid_days)}

    # Create variables for each course's selected section and enforce only one section per course
    course_section_vars = {}
    interval_vars = {}

    # For each course, create variables and constraints
    for course in courses:
        course_name = course["course"]
        sections = course["sections"]

        # Boolean variables to select only one section per course
        section_selector_vars = []
        section_intervals = []

        for idx, section in enumerate(sections):
            # Boolean variable for each section
            is_selected = model.NewBoolVar(f'section_selected_{course_name}_{idx}')
            section_selector_vars.append(is_selected)

            for day_key in ["day1", "day2"]:
                day_info = section[day_key]
                day = day_info["day"]

                if day not in valid_days:
                    continue

                start = parse_time_to_minutes(day_info["start"])
                end = parse_time_to_minutes(day_info["end"])
                duration = end - start

                # Create an optional interval variable for each day of the section
                interval = model.NewOptionalIntervalVar(
                    start, duration, end, is_selected, f'{course_name}_{day}_{day_key}_{idx}'
                )
                
                section_intervals.append((interval, is_selected))

        # Ensure only one section is chosen per course by setting the sum of section selector variables to 1
        model.Add(sum(section_selector_vars) == 1)

        # Store section selector variables in course_section_vars to track course section selection
        course_section_vars[course_name] = section_selector_vars
        interval_vars[course_name] = section_intervals

    # Constraint: prevent overlap of intervals for each day
    for day in valid_days:
        day_intervals = []

        for course, intervals in interval_vars.items():
            for interval, is_selected in intervals:
                # Check if the interval is for the current day
                if interval.Name().split("_")[1] == day:
                    day_intervals.append(interval)

        # Add NoOverlap constraint to ensure no conflicting intervals on the same day
        model.AddNoOverlap(day_intervals)

    # Objective: Maximize days_off and online_only_days
    days_off_vars = []
    online_only_days_vars = []
    num_days = len(valid_days)

    for day_idx in range(num_days):
        # Day off: no classes scheduled
        is_day_off = model.NewBoolVar(f'is_day_off_{day_idx}')
        model.Add(sum(is_selected for course in interval_vars for _, is_selected in interval_vars[course] if day == day_to_index[_.Name().split("_")[1]]) == 0).OnlyEnforceIf(is_day_off)
        days_off_vars.append(is_day_off)

        # Online-only day: only online classes
        is_online_only = model.NewBoolVar(f'is_online_only_{day_idx}')
        model.Add(sum(is_selected for course in interval_vars for _, is_selected in interval_vars[course] if day == day_to_index[_.Name().split("_")[1]]) > 0).OnlyEnforceIf(is_online_only)
        online_only_days_vars.append(is_online_only)

    # Objective to maximize the total number of days off and online-only days
    model.Maximize(sum(days_off_vars) + sum(online_only_days_vars))

    # Set a time limit for the solver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60  # Adjust the time limit as needed

    # Solve the model
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        selected_schedule = []
        for course in courses:
            course_name = course["course"]

            # Find the selected section by checking which boolean variable is True
            section_idx = next(idx for idx, var in enumerate(course_section_vars[course_name]) if solver.Value(var) == 1)
            selected_section = course["sections"][section_idx]

            # Only append if not already included
            if not any(sch["course"] == course_name for sch in selected_schedule):
                selected_schedule.append({
                    "course": course_name,
                    "day1": selected_section["day1"],
                    "day2": selected_section["day2"],
                    "professor": selected_section["professor"]
                })

        days_off = solver.Value(sum(days_off_vars))
        online_only_days = solver.Value(sum(online_only_days_vars))
        best_score = (days_off, online_only_days)

        return selected_schedule, best_score

    return None, None  # No valid schedule found

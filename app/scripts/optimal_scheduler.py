from ortools.sat.python import cp_model
from typing import List, Dict, Any, Tuple, Optional
model = cp_model.CpModel()

def parse_time_to_minutes(time_str: str) -> int:
    """
    Converts a time string in "HH:MM" format to total minutes since midnight.
    Args:
        time_str (str): Time string in "HH:MM" format (e.g., "13:30").
    Returns:
        int: Total minutes since midnight.
    """
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes

def generate_optimal_schedule(courses: List[Dict[str, Any]], exclude_weekend: bool = True) -> Optional[Tuple[List[Dict[str, Any]], Tuple[int, int]]]:
    """
    Generates the optimal schedule using Google OR-Tools CP-SAT solver.
    Args:
        courses (list): List of courses with their sections.
        exclude_weekend (bool): Whether to exclude weekends from scheduling.
    Returns:
        tuple: (best_schedule, best_score) where best_score is (days_off, online_only_days)
    """
    # Initialize the CP-SAT model
    model = cp_model.CpModel()

    # Define valid days based on whether weekends are excluded
    valid_days = ["M", "Tu", "W", "Th", "F"]
    if not exclude_weekend:
        valid_days.extend(["S", "Su"])  # Include Saturday and Sunday if weekends are allowed

    # Create mappings for days to indices for easier handling
    day_to_index = {day: idx for idx, day in enumerate(valid_days)}
    num_days = len(valid_days)

    # Define time slots (minutes in a day)
    total_minutes = 24 * 60  # Total minutes in a day

    # Variables to hold the selected section for each course
    course_section_vars = {}

    # Collect all variables for the solver
    all_vars = []

    # Dictionary to hold time intervals for each section
    section_time_intervals = {}

    # For each course, create variables and constraints
    for course_idx, course in enumerate(courses):
        course_name = course["course"]
        sections = course["sections"]

        # Create a variable to represent which section is selected for this course
        section_var = model.NewIntVar(0, len(sections) - 1, f'section_{course_name}')
        course_section_vars[course_name] = section_var
        all_vars.append(section_var)

        # Store the time intervals for each section of the course
        intervals = []

        for sec_idx, section in enumerate(sections):
            # Collect time intervals for day1 and day2
            section_intervals = []

            for day_info in [section["day1"], section["day2"]]:
                day = day_info["day"]
                if day not in valid_days:
                    continue  # Skip invalid days

                day_idx = day_to_index[day]
                start = parse_time_to_minutes(day_info["start"])
                end = parse_time_to_minutes(day_info["end"])

                # Append the interval (day index, start time, end time, format)
                section_intervals.append({
                    "day_idx": day_idx,
                    "start": start,
                    "end": end,
                    "format": day_info["format"]
                })

            intervals.append(section_intervals)

        # Store intervals for this course's sections
        section_time_intervals[course_name] = intervals

    # Add constraints to prevent time conflicts between courses
    for course1 in courses:
        course1_name = course1["course"]
        sections1 = course1["sections"]
        var1 = course_section_vars[course1_name]
        intervals1 = section_time_intervals[course1_name]

        for course2 in courses:
            course2_name = course2["course"]
            if course1_name >= course2_name:
                continue  # Avoid duplicate pairs and self-comparison

            sections2 = course2["sections"]
            var2 = course_section_vars[course2_name]
            intervals2 = section_time_intervals[course2_name]

            # For each possible pair of sections between two courses, prevent overlaps
            for idx1, times1 in enumerate(intervals1):
                for idx2, times2 in enumerate(intervals2):
                    # Check for possible overlaps
                    for t1 in times1:
                        for t2 in times2:
                            if t1["day_idx"] != t2["day_idx"]:
                                continue  # No conflict if days are different

                            # Overlap condition
                            latest_start = max(t1["start"], t2["start"])
                            earliest_end = min(t1["end"], t2["end"])

                            if latest_start < earliest_end:
                                # There is an overlap; add constraint to prevent both sections from being selected together
                                # This uses an implication: if var1 == idx1 and var2 == idx2 => conflict, so prevent this assignment
                                conflict = model.NewBoolVar(f'conflict_{course1_name}_{idx1}_{course2_name}_{idx2}')
                                model.Add(var1 == idx1).OnlyEnforceIf(conflict)
                                model.Add(var2 == idx2).OnlyEnforceIf(conflict)
                                model.AddImplication(conflict, model.NewBoolVar('false'))  # Conflict cannot happen

    # Objective: Maximize days off and online-only days
    # We need to compute days_off and online_only_days based on the selected sections
    # Since CP-SAT requires linear expressions, we'll approximate this by introducing additional variables

    # Create variables to count classes for each day and format
    day_format_counts = {}  # (day_idx, format) -> IntVar

    for day_idx in range(num_days):
        for fmt in ["online", "in-person"]:
            var = model.NewIntVar(0, len(courses), f'day_{day_idx}_{fmt}')
            day_format_counts[(day_idx, fmt)] = var

    # Add constraints to compute day_format_counts based on selected sections
    for course in courses:
        course_name = course["course"]
        var = course_section_vars[course_name]
        sections = course["sections"]
        intervals = section_time_intervals[course_name]

        for idx, times in enumerate(intervals):
            for time_info in times:
                day_idx = time_info["day_idx"]
                fmt = time_info["format"]

                # Create indicator variable: is this section selected?
                is_selected = model.NewBoolVar(f'is_selected_{course_name}_{idx}')
                model.Add(var == idx).OnlyEnforceIf(is_selected)
                model.Add(var != idx).OnlyEnforceIf(is_selected.Not())

                # Increment day_format_counts accordingly
                count_var = day_format_counts[(day_idx, fmt)]
                model.Add(count_var >= is_selected)

    # Variables to count days_off and online_only_days
    days_off_vars = []
    online_only_days_vars = []

    for day_idx in range(num_days):
        # Total classes for the day
        online_classes = day_format_counts[(day_idx, "online")]
        in_person_classes = day_format_counts[(day_idx, "in-person")]

        # Day off: both online and in-person classes are zero
        is_day_off = model.NewBoolVar(f'is_day_off_{day_idx}')
        model.Add(online_classes == 0).OnlyEnforceIf(is_day_off)
        model.Add(online_classes != 0).OnlyEnforceIf(is_day_off.Not())
        model.Add(in_person_classes == 0).OnlyEnforceIf(is_day_off)
        model.Add(in_person_classes != 0).OnlyEnforceIf(is_day_off.Not())
        days_off_vars.append(is_day_off)

        # Online-only day: in-person classes are zero, online classes > 0
        is_online_only = model.NewBoolVar(f'is_online_only_{day_idx}')
        model.Add(in_person_classes == 0).OnlyEnforceIf(is_online_only)
        model.Add(in_person_classes != 0).OnlyEnforceIf(is_online_only.Not())
        model.Add(online_classes > 0).OnlyEnforceIf(is_online_only)
        model.Add(online_classes == 0).OnlyEnforceIf(is_online_only.Not())
        online_only_days_vars.append(is_online_only)

    # Objective function: Maximize total days_off and online_only_days
    # We can give weights to prioritize days_off over online_only_days or vice versa
    # For this example, we'll give equal weights

    total_days_off = model.NewIntVar(0, num_days, 'total_days_off')
    model.Add(total_days_off == sum(days_off_vars))

    total_online_only_days = model.NewIntVar(0, num_days, 'total_online_only_days')
    model.Add(total_online_only_days == sum(online_only_days_vars))

    # Set the objective
    model.Maximize(total_days_off * num_days + total_online_only_days)

    # Create the solver and solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        # Extract the selected sections for each course
        selected_schedule = []
        for course in courses:
            course_name = course["course"]
            var = course_section_vars[course_name]
            selected_idx = solver.Value(var)
            selected_section = course["sections"][selected_idx]
            selected_schedule.append({
                "course": course_name,
                "day1": selected_section["day1"],
                "day2": selected_section["day2"],
                "professor": selected_section["professor"]
            })

        # Compute the best score
        days_off = solver.Value(total_days_off)
        online_only_days = solver.Value(total_online_only_days)
        best_score = (days_off, online_only_days)

        return selected_schedule, best_score
    else:
        return None  # No valid schedule found

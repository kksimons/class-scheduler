import itertools
import time

"""
Possible combinations with 5 courses, each with 5 sections, there are 5^5 = 3125 combinations.
We set a time limit in the code to attempt to mitigate this but at the cost of potentially missing optimal solutions.

Not DP
Uses itertools.product to generate all possible combinations of course sections.
Iteratively checks each combination for scheduling conflicts.
Evaluates and keeps track of the best schedule found based on certain criteria.
Does not store intermediate results to avoid redundant computations.

NOT LCG
LCG is a hybrid approach combining CP and SAT solving.
Constraints are posted at a high level, and conflicts during search lead to the generation of clauses (nogoods) to prevent similar conflicts in the future.
Nogoods are partial assignments that are known to lead to conflicts and are stored to prevent the solver from revisiting them.
We do not not generate clauses or nogoods, analyze conflicts to improve future search steps but instead simply skips over combinations where conflicts are found.

NOT SAT
Involves encoding a problem into a boolean formula and determining if there is an assignment of truth values to variables that satisfies the formula.
Uses advanced algorithms like the DPLL algorithm, clause learning, and heuristics for variable selection.
We do not encode the problem into a boolean formula or use SAT solvers or related algorithms.
Instead rely on procedural checks for scheduling conflicts.

NOT CP Model
Does not explicitly define variables and domains in the CP sense.
Does not use constraint propagation or specialized CP solvers.
Performs an exhaustive (though time-limited) search over all combinations.
The code solves a CSP but does not employ CP methodologies. Therefore, it is not considered a CP model.
Uses simple boolean flags (e.g., day_vector with 0 or 1 to represent free or occupied time slots).
Does not model the problem using high-level boolean variables and constraints in the way CP models do.

In CP, atomic constraints are the basic building blocks that specify relationships between variables (e.g., X != Y, X + Y <= Z).
These are used by CP solvers to enforce consistency and prune the search space.

We implement constraints implicitly through checks (e.g., time conflicts).
But do not define atomic constraints between variables.
Constraints are procedural (checking time overlaps) rather than declarative.

We perform an exhaustive search over possible combinations (within a time limit).
Could use advanced optimization techniques to efficiently handle larger datasets.
"""

def parse_time(time_str):
    """
    Converts a time string in "HH:MM" format to total minutes since midnight.
    We are receiving 24 hour format from the client and gets us an integer for easy comparisons.
    Args:
        time_str (str): Time string in "HH:MM" format (e.g., "13:30").
    Returns:
        int: Total minutes since midnight.
    """
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes

def mark_time(day_vector, start, end):
    """
    Marks the time slots in the day_vector as occupied between start and end times.
    Args:
        day_vector (list): List representing each minute of the day (1440 minutes total).
        We use a boolean to set whether a time slot is free (0), or occupied (1).
        start (int): Start time in minutes since midnight.
        end (int): End time in minutes since midnight.
    """
    for minute in range(start, end):
        day_vector[minute] = 1

def is_free(day_vector, start, end):
    """
    Checks if the time slot between start and end is free (true, else returns false) in the day_vector by iterating over each minute from the start and end time.
    Args:
        day_vector (list): List representing each minute of the day.
        start (int): Start time in minutes since midnight.
        end (int): End time in minutes since midnight.
    Returns:
        bool: True if the time slot is free, False otherwise.
    """
    return all(day_vector[minute] == 0 for minute in range(start, end))

def evaluate_schedule(schedule):
    """
    Evaluates the schedule based on the number of days off and online-only days.
    Args:
        schedule (list): List of scheduled sections.
    Returns:
        tuple: (days_off, online_only_days)
    """
    # Define the weekdays
    weekdays = {"M", "Tu", "W", "Th", "F"}

    # Initialize a dictionary to count classes for each weekday
    day_classes = {day: {"online": 0, "in-person": 0} for day in weekdays}

    # Iterate over each section in the schedule
    for section in schedule:
        # Check both day1 and day2 information
        for day_key in ["day1", "day2"]:
            day_info = section.get(day_key)
            if day_info and day_info["day"] in weekdays:
                # Increment the class count based on the format (online or in-person)
                day_classes[day_info["day"]][day_info["format"]] += 1

    # Calculate the number of days off (no classes scheduled)
    days_off = sum(
        1 for day, classes in day_classes.items()
        if all(v == 0 for v in classes.values())
    )

    # Calculate the number of days with only online classes
    online_only_days = sum(
        1 for day, classes in day_classes.items()
        if classes["in-person"] == 0 and classes["online"] > 0
    )

    return days_off, online_only_days

def generate_optimal_schedule(courses, time_limit=30, exclude_weekend=True):
    """
    Generates the optimal schedule by exploring all possible combinations of course sections.
    Args:
        courses (list): List of courses with their sections.
        time_limit (int): Maximum time allowed for schedule generation (in seconds).
        exclude_weekend (bool): Whether to exclude weekends from scheduling.
    Returns:
        tuple: (best_schedule, best_score) where best_score is (days_off, online_only_days)
    """
    start_time = time.time()  # Record the start time to enforce the time limit
    best_schedule = []        # Initialize the best schedule found so far
    best_score = (0, 0)       # Initialize the best score (days_off, online_only_days)

    # Define valid days based on whether weekends are excluded
    valid_days = {"M", "Tu", "W", "Th", "F"}
    if not exclude_weekend:
        valid_days.update({"S", "Su"})  # Include Saturday and Sunday if weekends are allowed

    # Generate all possible combinations of course sections
    # Each course must have at least one section
    course_sections = [course["sections"] for course in courses]
    for course_combination in itertools.product(*course_sections):
        # Check if the time limit has been exceeded
        if time.time() - start_time > time_limit:
            break  # Exit the loop if time limit is exceeded

        # Initialize day vectors for each valid day
        # Each day vector represents each minute of the day (1440 minutes)
        day_vectors = {day: [0] * (24 * 60) for day in valid_days}

        structured_schedule = []  # List to store the scheduled sections
        conflict_found = False    # Flag to indicate if a conflict is found
        scheduled_courses = set() # Set to track courses that have been scheduled

        # Iterate over each section in the current combination
        for idx, section in enumerate(course_combination):
            course_name = courses[idx]["course"]  # Get the course name

            # Skip if this course is already scheduled (prevents duplicate scheduling)
            if course_name in scheduled_courses:
                continue  # Move to the next section

            professor = section["professor"]
            day1 = section["day1"]
            day2 = section["day2"]

            # Check both day1 and day2 for scheduling conflicts
            for day_info in [day1, day2]:
                day = day_info["day"]
                if day not in valid_days:
                    conflict_found = True  # Invalid day found
                    break  # Exit the loop

                # Convert start and end times to minutes since midnight
                start = parse_time(day_info["start"])
                end = parse_time(day_info["end"])

                # Check if the time slot is free on that day
                if not is_free(day_vectors[day], start, end):
                    conflict_found = True  # Time conflict found
                    break  # Exit the loop

            if conflict_found:
                break  # Exit the loop if any conflict is found

            # Mark the occupied time slots for each day in the section
            for day_info in [day1, day2]:
                day = day_info["day"]
                if day in valid_days:
                    start = parse_time(day_info["start"])
                    end = parse_time(day_info["end"])
                    mark_time(day_vectors[day], start, end)  # Mark time as occupied

            # Add the section to the structured schedule
            structured_schedule.append({
                "course": course_name,
                "day1": day1,
                "day2": day2,
                "professor": professor
            })
            scheduled_courses.add(course_name)  # Mark the course as scheduled

        if conflict_found:
            continue  # Skip to the next combination if a conflict is found

        # Evaluate the current schedule based on days off and online-only days
        days_off, online_only_days = evaluate_schedule(structured_schedule)

        # Update the best schedule if the current one has a better score
        if (days_off, online_only_days) > best_score:
            best_schedule = structured_schedule
            best_score = (days_off, online_only_days)

    # Return the best schedule and its score
    if best_schedule:
        return best_schedule, best_score
    else:
        return None, None  # No valid schedule found within the time limit

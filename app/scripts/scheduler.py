from ortools.sat.python import cp_model
import json

def create_class_scheduling_model(courses):
    model = cp_model.CpModel()
    shifts = {}

    # Create a single boolean variable per section representing its selection (both days)
    for course_idx, course in enumerate(courses):
        section_vars = []
        
        for sec_idx, section in enumerate(course.sections):
            # Define a single boolean variable for the entire section
            section_selected = model.NewBoolVar(f"course_{course_idx}_sec_{sec_idx}_selected")
            shifts[(course_idx, sec_idx)] = section_selected
            section_vars.append(section_selected)

            # Apply format constraints if specified for each day in the section
            if section.day1.format == "online":
                day1_selected = model.NewBoolVar(f"course_{course_idx}_sec_{sec_idx}_day1_online")
                model.Add(day1_selected == 1).OnlyEnforceIf(section_selected)
            if section.day2.format == "online":
                day2_selected = model.NewBoolVar(f"course_{course_idx}_sec_{sec_idx}_day2_online")
                model.Add(day2_selected == 1).OnlyEnforceIf(section_selected)

        # Enforce that only one section is selected per course
        model.Add(sum(section_vars) == 1)

    # Add variables for preferences (day off, online-only day)
    num_days = 7  # Assuming a week (0 to 6 for Mon to Sun)
    day_off_vars = [model.NewBoolVar(f"day_off_{day}") for day in range(num_days)]
    online_day_vars = [model.NewBoolVar(f"online_day_{day}") for day in range(num_days)]

    for day in range(num_days):
        classes_on_day = []
        online_classes_on_day = []

        # Collect classes for each day across all sections
        for course_idx, course in enumerate(courses):
            for sec_idx, section in enumerate(course.sections):
                if section.day1.day == day:
                    classes_on_day.append(shifts[(course_idx, sec_idx)])
                    if section.day1.format == "online":
                        online_classes_on_day.append(shifts[(course_idx, sec_idx)])
                if section.day2.day == day:
                    classes_on_day.append(shifts[(course_idx, sec_idx)])
                    if section.day2.format == "online":
                        online_classes_on_day.append(shifts[(course_idx, sec_idx)])

        # Enforce day off if no classes are scheduled
        model.Add(sum(classes_on_day) == 0).OnlyEnforceIf(day_off_vars[day])

        # Enforce online-only day if all classes are online
        model.Add(sum(classes_on_day) == sum(online_classes_on_day)).OnlyEnforceIf(online_day_vars[day])

    # Maximize preferences for having a day off or an online-only day
    model.Maximize(sum(day_off_vars) * 2 + sum(online_day_vars))

    # Prevent overlapping classes on the same day across courses
    for course_idx, course in enumerate(courses):
        for sec_idx, section in enumerate(course.sections):
            for other_course_idx, other_course in enumerate(courses):
                if course_idx >= other_course_idx:
                    continue
                for other_sec_idx, other_section in enumerate(other_course.sections):
                    # Check overlap for each day in the section
                    if section.day1.day == other_section.day1.day and section.day1.end > other_section.day1.start and section.day1.start < other_section.day1.end:
                        model.AddBoolOr([shifts[(course_idx, sec_idx)].Not(), shifts[(other_course_idx, other_sec_idx)].Not()])

                    if section.day2.day == other_section.day2.day and section.day2.end > other_section.day2.start and section.day2.start < other_section.day2.end:
                        model.AddBoolOr([shifts[(course_idx, sec_idx)].Not(), shifts[(other_course_idx, other_sec_idx)].Not()])

    return model, shifts


def solve_class_scheduling(model, shifts, courses):
    solver = cp_model.CpSolver()

    class SolutionPrinter(cp_model.CpSolverSolutionCallback):
        def __init__(self, shifts, courses):
            super().__init__()
            self._shifts = shifts
            self._courses = courses
            self._solution_count = 0
            self._result = None

        def on_solution_callback(self):
            if self._solution_count >= 1:
                self.StopSearch()
                return

            self._solution_count += 1
            result = {}

            for (course_idx, sec_idx), var in self._shifts.items():
                if self.Value(var) == 1:
                    section = self._courses[course_idx].sections[sec_idx]
                    result[f"course_{course_idx}_sec_{sec_idx}"] = {
                        "day1": {
                            "day": section.day1.day,
                            "start": section.day1.start,
                            "end": section.day1.end,
                            "format": section.day1.format
                        },
                        "day2": {
                            "day": section.day2.day,
                            "start": section.day2.start,
                            "end": section.day2.end,
                            "format": section.day2.format
                        },
                        "professor": section.professor
                    }

            self._result = result
            print(f"Solution {self._solution_count}: {json.dumps(result, indent=2)}")

        def get_result(self):
            return self._result

    solution_printer = SolutionPrinter(shifts, courses)
    solver.SolveWithSolutionCallback(model, solution_printer)
    return solution_printer.get_result()

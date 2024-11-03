from ortools.sat.python import cp_model
import json

def create_class_scheduling_model(courses):
    model = cp_model.CpModel()
    section_selected_vars = {}

    # Create a single boolean variable per section representing its selection (both days)
    for course_idx, course in enumerate(courses):
        section_vars = []
        
        for sec_idx, section in enumerate(course.sections):
            # Define a single boolean variable for the entire section
            section_selected = model.NewBoolVar(f"course_{course_idx}_sec_{sec_idx}_selected")
            section_selected_vars[(course_idx, sec_idx)] = section_selected
            section_vars.append(section_selected)

        # Constraint: Only one section can be selected per course
        model.Add(sum(section_vars) == 1)

        # Additional constraint: Only one day1 and day2 per course based on the selected section
        # This ensures that each course has exactly one unique day1 and day2.
        for sec_idx, section in enumerate(course.sections):
            for day_name, day_info in {"day1": section.day1, "day2": section.day2}.items():
                day_selected = model.NewBoolVar(f"course_{course_idx}_{day_name}_selected")
                
                # Ensure that day1/day2 is only selected if the corresponding section is selected
                model.Add(day_selected == 1).OnlyEnforceIf(section_selected_vars[(course_idx, sec_idx)])

    # Add preferences for day off and online-only day
    num_days = 7  # Assuming a week (0 to 6 for Mon to Sun)
    day_off_vars = [model.NewBoolVar(f"day_off_{day}") for day in range(num_days)]
    online_day_vars = [model.NewBoolVar(f"online_day_{day}") for day in range(num_days)]

    # Prevent overlapping classes on the same day across courses
    for course_idx, course in enumerate(courses):
        for sec_idx, section in enumerate(course.sections):
            for other_course_idx, other_course in enumerate(courses):
                if course_idx >= other_course_idx:
                    continue
                for other_sec_idx, other_section in enumerate(other_course.sections):
                    # Only check overlaps if both sections are selected
                    if section.day1.day == other_section.day1.day:
                        model.AddBoolOr([
                            section_selected_vars[(course_idx, sec_idx)].Not(),
                            section_selected_vars[(other_course_idx, other_sec_idx)].Not()
                        ])

                    if section.day2.day == other_section.day2.day:
                        model.AddBoolOr([
                            section_selected_vars[(course_idx, sec_idx)].Not(),
                            section_selected_vars[(other_course_idx, other_sec_idx)].Not()
                        ])

    return model, section_selected_vars

def solve_class_scheduling(model, section_selected_vars, courses):
    solver = cp_model.CpSolver()

    class SolutionPrinter(cp_model.CpSolverSolutionCallback):
        def __init__(self, section_selected_vars, courses):
            super().__init__()
            self._section_selected_vars = section_selected_vars
            self._courses = courses
            self._solution_count = 0
            self._result = None

        def on_solution_callback(self):
            if self._solution_count >= 1:
                self.StopSearch()
                return

            self._solution_count += 1
            result = {}

            for (course_idx, sec_idx), var in self._section_selected_vars.items():
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

    solution_printer = SolutionPrinter(section_selected_vars, courses)
    solver.SolveWithSolutionCallback(model, solution_printer)
    return solution_printer.get_result()

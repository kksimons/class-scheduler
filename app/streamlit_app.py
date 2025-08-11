import streamlit as st
import requests
import json

API_URL = "http://localhost:80/api/v1/class-scheduler"
headers = {"Content-Type": "application/json"}

st.title("Class Scheduler")

# Persistent state for courses using Streamlit session state
if "courses" not in st.session_state:
    st.session_state["courses"] = []

# Add new course
if st.button("Add New Course"):
    st.session_state["courses"].append({"course": "", "sections": []})

# Display each course and its sections
for i, course in enumerate(st.session_state["courses"]):
    # Course name input
    course_name = st.text_input(f"Course {i + 1} Name", key=f"course_name_{i}")
    st.session_state["courses"][i]["course"] = course_name

    # Add new section for this course
    if st.button(f"Add Section for {course_name}", key=f"add_section_{i}"):
        st.session_state["courses"][i]["sections"].append(
            {
                "days": [],
                "professor": "",
            }
        )

    # Display each section with inputs for day1 and day2
    for j, section in enumerate(course["sections"]):
        day1_day = st.selectbox(
            f"Course {i + 1} Section {j + 1} Day 1",
            ["M", "Tu", "W", "Th", "F", "S"],
            key=f"day1_day_{i}_{j}",
        )
        day1_start = st.text_input(
            f"Course {i + 1} Section {j + 1} Day 1 Start (e.g., 13:00)",
            key=f"day1_start_{i}_{j}",
        )
        day1_end = st.text_input(
            f"Course {i + 1} Section {j + 1} Day 1 End (e.g., 15:50)",
            key=f"day1_end_{i}_{j}",
        )
        day1_format = st.selectbox(
            f"Course {i + 1} Section {j + 1} Day 1 Format",
            ["in-person", "online"],
            key=f"day1_format_{i}_{j}",
        )

        day2_day = st.selectbox(
            f"Course {i + 1} Section {j + 1} Day 2",
            ["M", "Tu", "W", "Th", "F", "S"],
            key=f"day2_day_{i}_{j}",
        )
        day2_start = st.text_input(
            f"Course {i + 1} Section {j + 1} Day 2 Start (e.g., 13:00)",
            key=f"day2_start_{i}_{j}",
        )
        day2_end = st.text_input(
            f"Course {i + 1} Section {j + 1} Day 2 End (e.g., 15:50)",
            key=f"day2_end_{i}_{j}",
        )
        day2_format = st.selectbox(
            f"Course {i + 1} Section {j + 1} Day 2 Format",
            ["in-person", "online"],
            key=f"day2_format_{i}_{j}",
        )

        professor = st.text_input(
            f"Course {i + 1} Section {j + 1} Professor", key=f"professor_{i}_{j}"
        )

        # Update section data in session state
        st.session_state["courses"][i]["sections"][j] = {
            "day1": {
                "day": day1_day,
                "start": day1_start,
                "end": day1_end,
                "format": day1_format,
            },
            "day2": {
                "day": day2_day,
                "start": day2_start,
                "end": day2_end,
                "format": day2_format,
            },
            "professor": professor,
        }

# Generate schedule button
if st.button("Generate Schedule"):
    data = {"courses": st.session_state["courses"]}
    with st.spinner("Generating schedule..."):
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code == 200:
            output = response.json()
            st.success("Schedule generated successfully!")
            st.json(output)  # Display output as JSON
        else:
            st.error(f"Failed to generate schedule. Error: {response.status_code}")
            st.write(response.text)

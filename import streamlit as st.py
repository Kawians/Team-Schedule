import streamlit as st
import pandas as pd
import numpy as np

# Define shift structure & break rules
shifts = {
    "Toronto (8 AM - 4 PM)": {"start": 8, "end": 16, "breaks": [10, 14], "lunch_range": (11.5, 13)},
    "Toronto (10 AM - 6 PM)": {"start": 10, "end": 18, "breaks": [12, 16], "lunch_range": (12.5, 14)},
    "Bogotá (7 AM - 4:30 PM)": {"start": 7, "end": 16.5, "breaks": [10], "lunch_range": (11.5, 13.5)},
    "Bogotá (8:30 AM - 6 PM)": {"start": 8.5, "end": 18, "breaks": [11], "lunch_range": (12, 14)}
}

# Peak hours
peak_hours = [(10.5, 12.5), (14.5, 16.5)]

# Sidebar input
st.sidebar.header("Step 1: Enter Employees Per Shift")
employees_per_shift = {
    shift: st.sidebar.number_input(f"{shift}", min_value=0, step=1, value=3)
    for shift in shifts.keys()
}

# Button to generate schedule
if st.sidebar.button("Generate Schedule"):
    schedule_data = []

    for shift, num_employees in employees_per_shift.items():
        shift_info = shifts[shift]
        lunch_start, lunch_end = shift_info["lunch_range"]

        # Staggered break & lunch assignment
        break_intervals = np.linspace(lunch_start, lunch_end, num_employees)  # Staggered lunch
        break_intervals = [round(b, 1) for b in break_intervals]

        for i in range(num_employees):
            assigned_lunch = break_intervals[i]
            schedule_data.append([
                shift, f"Employee {i+1}", shift_info["start"], shift_info["end"],
                shift_info["breaks"], f"{assigned_lunch}:00 - {assigned_lunch + 0.5}:00"
            ])

    df_schedule = pd.DataFrame(schedule_data, columns=["Shift", "Employee", "Start Time", "End Time", "Breaks", "Lunch"])

    # Store in session state for modifications
    if "df_schedule" not in st.session_state:
        st.session_state.df_schedule = df_schedule.copy()

# If a schedule exists, show it with live adjustments
if "df_schedule" in st.session_state:
    st.subheader("Step 2: Adjust Shifts, Breaks & Lunch Live")

    df_schedule = st.session_state.df_schedule

    for i in range(len(df_schedule)):
        shift_info = shifts[df_schedule.at[i, "Shift"]]
        min_start, max_end = shift_info["start"], shift_info["end"]
        lunch_start, lunch_end = shift_info["lunch_range"]

        # Shift timing sliders
        df_schedule.at[i, "Start Time"] = st.slider(
            f"{df_schedule.at[i, 'Employee']} ({df_schedule.at[i, 'Shift']}) Start Time",
            min_value=float(min_start), max_value=float(max_end - 1), step=0.5, value=float(df_schedule.at[i, "Start Time"])
            )

        df_schedule.at[i, "End Time"] = st.slider(
            f"{df_schedule.at[i, 'Employee']} ({df_schedule.at[i, 'Shift']}) End Time",
            min_value=float(df_schedule.at[i, "Start Time"] + 1),
            max_value=float(max_end), step=0.5, value=float(df_schedule.at[i, "End Time"])
            )

        # Lunch adjustment slider
        lunch_time = float(df_schedule.at[i, "Lunch"].split("-")[0].strip().replace(":00", ""))
        new_lunch_time = st.slider(
            f"{df_schedule.at[i, 'Employee']} ({df_schedule.at[i, 'Shift']}) Lunch Time",
            min_value=float(lunch_start), max_value=float(lunch_end - 0.5), step=0.5, value=float(lunch_time)
            )
        df_schedule.at[i, "Lunch"] = f"{new_lunch_time}:00 - {new_lunch_time + 0.5}:00"

    # Display final schedule
    st.subheader("Final Schedule with Adjustments")
    st.write(df_schedule)

    # Export updated schedule as Excel
    excel_file = "updated_schedule.xlsx"
    df_schedule.to_excel(excel_file, index=False)

    # Provide download button
    with open(excel_file, "rb") as f:
        st.download_button("Download Updated Schedule as Excel", f, file_name=excel_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
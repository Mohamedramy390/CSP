
#
# Intelligent Systems Project 1:
# Final script with enhanced backtracking visibility.
#


import pandas as pd
from itertools import product
import os
from collections import deque
import tkinter as tk
from tkinter import ttk

# --- 1. DATA LOADING ---

def load_data_from_csv(folder_path):
    """
    Reads all required CSV files from a specified folder into a dictionary of DataFrames.
    """
    try:
        file_names = {
            'courses': 'Courses.csv',
            'instructors': 'Instructor.csv',
            'rooms': 'Rooms.csv',
            'timeslots': 'TimeSlots.csv',
            'sections': 'Sections.csv'
        }
        data = {}
        print("--- Loading Data ---")
        for key, name in file_names.items():
            full_path = os.path.join(folder_path, name)
            print(f"  -> Reading {name}...")
            data[key] = pd.read_csv(full_path)

        if 'TimeSlotID' not in data['timeslots'].columns:
            print("  -> 'TimeSlotID' not found. Generating it automatically.")
            data['timeslots']['TimeSlotID'] = [f'TS{i}' for i in range(len(data['timeslots']))]
        if 'SecrionID' in data['sections'].columns:
            data['sections'].rename(columns={'SecrionID': 'SectionID'}, inplace=True)

        print("✅ All CSV files loaded successfully!")
        return data
    except FileNotFoundError as e:
        print(f"❌ ERROR: File not found. Details: {e}")
        return None
    except Exception as e:
        print(f"❌ An error occurred during data loading: {e}")
        return None

# --- HELPER & GUI FUNCTIONS ---

def create_day_to_slots_map(timeslots_df):
    """Creates a dictionary mapping each day to a list of its TimeSlotIDs."""
    return timeslots_df.groupby('Day')['TimeSlotID'].apply(list).to_dict()

def display_timetable_grid_gui(schedule_df):
    """
    Creates a GUI window with the timetable in a grid format (Timeslot vs Section),
    with sections arranged by level (L1, L2, etc.).
    """
    if schedule_df is None or schedule_df.empty:
        print(" -> No schedule to display in GUI.")
        return

    # Prepare data
    schedule_df['TimeSlot'] = schedule_df['Day'] + " " + schedule_df['Time']
    schedule_df['CellContent'] = schedule_df['Course'] + "\n" + schedule_df['Instructor']

    timetable_grid = schedule_df.pivot_table(
        index='TimeSlot',
        columns='Section',
        values='CellContent',
        aggfunc='first'
    ).fillna('')

    # --- Sort by day order and level ---
    day_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Saturday"]

    timetable_grid = timetable_grid.reset_index()
    timetable_grid['Day'] = timetable_grid['TimeSlot'].apply(lambda x: x.split(' ')[0])
    timetable_grid['Day'] = pd.Categorical(timetable_grid['Day'], categories=day_order, ordered=True)
    timetable_grid = timetable_grid.sort_values(['Day', 'TimeSlot']).drop('Day', axis=1).set_index('TimeSlot')

    # --- Sort columns (sections) by level ---
    def get_level(section_name):
        import re
        match = re.search(r"L(\d+)", section_name)
        return int(match.group(1)) if match else 999

    sorted_columns = sorted(timetable_grid.columns, key=get_level)
    timetable_grid = timetable_grid[sorted_columns]

    # --- GUI Setup ---
    window = tk.Tk()
    window.title("Generated Timetable (Arranged by Level)")
    window.geometry("1200x700")

    frame = tk.Frame(window)
    frame.pack(expand=True, fill='both')

    style = ttk.Style()
    style.configure("Treeview", rowheight=45)
    style.configure("Treeview.Heading", font=('Calibri', 11, 'bold'))

    tree = ttk.Treeview(frame, style="Treeview")

    columns = ['TimeSlot'] + list(timetable_grid.columns)
    tree["columns"] = columns
    tree["show"] = "headings"

    for col in columns:
        tree.heading(col, text=col)
        width = 220 if col == 'TimeSlot' else 160
        tree.column(col, anchor="center", width=width, stretch=False)

    for index, row in timetable_grid.iterrows():
        values = [index] + list(row)
        tree.insert("", tk.END, values=values)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tree.pack(side="left", expand=True, fill="both")

    window.mainloop()


# --- 2. CSP FORMULATION AND SETUP ---

def setup_csp(data):
    """
    Sets up the CSP variables and domains, creating separate variables for lecture and lab parts.
    """
    variables, domains, empty_domain_reasons = [], {}, {}
    day_to_slots = create_day_to_slots_map(data['timeslots'])

    print("\n--- Formulating CSP ---")
    for _, section in data['sections'].iterrows():
        student_count = section['StudentCount']
        courses_for_section = [c.strip() for c in str(section['Courses']).split(',') if c.strip()]
        for course_id in courses_for_section:
            if course_id not in data['courses']['CourseID'].values:
                print(f"  -> 🔴 WARNING: CourseID '{course_id}' from Sections.csv not found in Courses.csv. Skipping.")
                continue

            course_info = data['courses'][data['courses']['CourseID'] == course_id].iloc[0]
            course_type = course_info['Type']
            qualified_instructors = data['instructors'][data['instructors']['QualifiedCourses'].apply(lambda x: course_id in str(x))]
            
            def create_domain_for_type(var_type):
                domain = []
                if var_type == "Lecture":
                    possible_rooms = data['rooms'][(data['rooms']['Type'] == 'Lecture') & (data['rooms']['Capacity'] >= student_count)]
                    possible_inst = qualified_instructors[qualified_instructors['InstructorID'].str.startswith('PROF')]
                    if not possible_rooms.empty and not possible_inst.empty:
                        domain = list(product(data['timeslots']['TimeSlotID'], possible_rooms['RoomID'], possible_inst['InstructorID']))
                elif var_type == "Lab":
                    possible_rooms = data['rooms'][(data['rooms']['Type'] == 'Lab') & (data['rooms']['Capacity'] >= student_count)]
                    possible_inst = qualified_instructors[qualified_instructors['InstructorID'].str.startswith('AP')]
                    if not possible_rooms.empty and not possible_inst.empty:
                        domain = list(product(data['timeslots']['TimeSlotID'], possible_rooms['RoomID'], possible_inst['InstructorID']))
                return domain

            var_types_to_create = ["Lecture", "Lab"] if course_type == "Lecture and Lab" else [course_type]

            for var_type in var_types_to_create:
                variable = f"{course_id}_{var_type}_{section['SectionID']}"
                variables.append(variable)
                
                initial_domain = create_domain_for_type(var_type)
                
                final_domain = []
                for timeslot_id, room_id, instructor_id in initial_domain:
                    instructor_info = data['instructors'].loc[data['instructors']['InstructorID'] == instructor_id].iloc[0]
                    preference = instructor_info.get('PreferredSlots', 'Anytime')
                    if preference and "Not on" in str(preference):
                        forbidden_day = preference.split("Not on ")[-1].strip()
                        if timeslot_id in day_to_slots.get(forbidden_day, []): continue
                    final_domain.append((timeslot_id, room_id, instructor_id))
                
                domains[variable] = final_domain

                if not final_domain:
                    reason = f"No valid (Room, Instructor, Time) combination found for the {var_type} part of course '{course_id}'."
                    print(f"  -> 🔴 WARNING for [{variable}]: Domain is empty. Reason: {reason}")
                    empty_domain_reasons[variable] = reason
    
    print(" -> Done.")
    constraints = [(v1, v2) for i, v1 in enumerate(variables) for v2 in variables[i+1:]]
    return variables, domains, constraints, empty_domain_reasons

# --- 3. ARC CONSISTENCY (AC-3 ALGORITHM) ---
def is_consistent(var1_assignment, var2_assignment, var1, var2):
    time1, room1, instructor1 = var1_assignment
    time2, room2, instructor2 = var2_assignment
    if time1 == time2 and (instructor1 == instructor2 or room1 == room2): return False
    section1 = '_'.join(var1.split('_')[2:])
    section2 = '_'.join(var2.split('_')[2:])
    if time1 == time2 and section1 == section2: return False
    return True

def revise(domains, var1, var2):
    revised = False
    initial_size = len(domains[var1])
    domains[var1] = [val1 for val1 in domains[var1] if any(is_consistent(val1, val2, var1, var2) for val2 in domains[var2])]
    return len(domains[var1]) < initial_size

def ac3(variables, domains, constraints):
    queue = deque(constraints + [(v2, v1) for v1, v2 in constraints])
    while queue:
        var1, var2 = queue.popleft()
        if revise(domains, var1, var2):
            if not domains[var1]: return False
            for neighbor in [v for v in variables if v != var1 and v != var2]:
                queue.append((neighbor, var1))
    return True

# --- 4. BACKTRACKING SOLVER WITH MRV (AND DEBUG PRINTING) ---
def select_unassigned_variable_mrv(variables, schedule, domains):
    unassigned = [v for v in variables if v not in schedule]
    return min(unassigned, key=lambda var: len(domains[var])) if unassigned else None

def solve_backtracking(variables, domains, schedule):
    if len(schedule) == len(variables): return schedule
    variable = select_unassigned_variable_mrv(variables, schedule, domains)
    if variable is None: return None

    # --- ADDED: Progress indicator ---
    print(f" -> Trying to schedule: {variable} ({len(schedule) + 1}/{len(variables)})")

    for value in domains[variable]:
        if all(is_consistent(value, val, variable, var) for var, val in schedule.items()):
            schedule[variable] = value

            # --- ADDED: Success indicator ---
            print(f"  -> SUCCESS: Placed {variable} at {value[0]}")
            
            result = solve_backtracking(variables, domains, schedule)
            if result: return result
            
            del schedule[variable] # Backtrack
            
    return None

# --- 5. DISPLAY AND SAVE TIMETABLE ---
def display_and_save_timetable(schedule, data, output_filename="timetable_output.csv"):
    if not schedule:
        print("\n❌ No feasible timetable could be found.")
        return

    timetable_data = []
    for variable, (time_id, room_id, instructor_id) in schedule.items():
        parts = variable.split('_')
        course_id, var_type, section_id_parts = parts[0], parts[1], '_'.join(parts[2:])
        
        course_name = data['courses'].loc[data['courses']['CourseID'] == course_id, 'CourseName'].iloc[0]
        time_details = data['timeslots'].loc[data['timeslots']['TimeSlotID'] == time_id].iloc[0]
        instructor_name = data['instructors'].loc[data['instructors']['InstructorID'] == instructor_id, 'Name'].iloc[0]
        time_str = f"{time_details.get('StartTime', '')} - {time_details.get('EndTime', '')}"
        display_course = f"{course_id} ({var_type})"
        
        timetable_data.append({'Day': time_details['Day'], 'Time': time_str, 'Section': section_id_parts, 'Course': display_course, 'Instructor': instructor_name})
    
    final_df = pd.DataFrame(timetable_data)
    
    print("\n✅ Feasible Timetable Generated Successfully!\n")
    print(final_df.sort_values(by=['Day', 'Time', 'Section']).to_string(index=False))
    final_df.to_csv(output_filename, index=False)
    print(f"\n✅ Timetable has been saved to '{output_filename}'")
        
    print("\n -> Launching GUI window...")
    display_timetable_grid_gui(final_df)

# --- NEW FUNCTION TO SAVE SETUP OUTPUT ---
def save_setup_to_file(variables, domains, empty_reasons, filename="csp_setup_output.txt"):
    """
    Saves the complete list of variables and their domains to an external file.
    """
    try:
        with open(filename, 'w') as f:
            f.write("--- CSP VARIABLES (LECTURES TO SCHEDULE) ---\n")
            f.write(f"Total: {len(variables)}\n\n")
            for var in sorted(variables): 
                f.write(f"{var}\n")

            f.write("\n\n--- CSP DOMAINS (ALL POSSIBLE ASSIGNMENTS) ---\n")
            for var in sorted(domains.keys()): 
                domain_values = domains[var]
                f.write(f"\n--- Domain for: {var} (Total Possibilities: {len(domain_values)}) ---\n")
                if not domain_values:
                    reason = empty_reasons.get(var, "No specific reason captured.")
                    f.write(f"  -> EMPTY DOMAIN. Reason: {reason}\n")
                else:
                    for value in domain_values:
                        f.write(f"  -> {value}\n")
        
        print(f"\n✅ CSP setup details have been saved to '{filename}'")
    except Exception as e:
        print(f"\n❌ Could not save the setup file. Error: {e}")


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    csv_folder_path = r"E:\CSP_data"
    dataset = load_data_from_csv(csv_folder_path)
    if dataset:
        csp_vars, csp_domains, csp_constraints, empty_reasons = setup_csp(dataset)
        
        # --- SAVE THE SETUP TO A FILE ---
        save_setup_to_file(csp_vars, csp_domains, empty_reasons)
        
        # --- CONTINUE WITH SOLVER ---
        print("\n--- 2. Enforcing Arc Consistency (AC-3) ---")
        if any(not d for d in csp_domains.values()):
             print(" -> Halting process because one or more domains are empty.")
        elif ac3(csp_vars, csp_domains, csp_constraints):
            print(" -> AC-3 successful. Domains have been pruned.")
            print("\n--- 3. Starting Solver (Backtracking + MRV) ---")
            final_schedule = solve_backtracking(csp_vars, csp_domains, {})
            display_and_save_timetable(final_schedule, dataset)
        else:
            print("❌ No solution possible. AC-3 found an inconsistency.")
#
# Intelligent Systems Project 1:
# Final version with lecture grouping and a clean, section-based GUI.
#

import pandas as pd
from itertools import product
import os
from collections import deque
import tkinter as tk
from tkinter import ttk
import re

# --- 1. DATA LOADING ---

def load_data_from_csv(folder_path):
    """
    Reads all required CSV files from a specified folder into a dictionary of DataFrames.
    """
    try:
        file_names = {
            'courses': 'Courses.csv', 'instructors': 'Instructor.csv', 'rooms': 'Rooms.csv',
            'timeslots': 'TimeSlots.csv', 'sections': 'Sections.csv'
        }
        data = {}
        print("--- Loading Data ---")
        for key, name in file_names.items():
            full_path = os.path.join(folder_path, name)
            print(f"  -> Reading {name}...")
            data[key] = pd.read_csv(full_path)

        if 'TimeSlotID' not in data['timeslots'].columns:
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
    Creates a GUI window with columns for each individual section, sorted by level.
    """
    if schedule_df is None or schedule_df.empty:
        print(" -> No schedule to display in GUI.")
        return

    # Prepare data for the pivot table
    schedule_df['TimeSlot'] = schedule_df['Day'] + " " + schedule_df['Time']
    schedule_df['CellContent'] = schedule_df['Course'] + "\n" + schedule_df['Instructor']

    timetable_grid = schedule_df.pivot_table(
        index='TimeSlot',
        columns='Section',
        values='CellContent',
        aggfunc='first'
    ).fillna('')

    # Sort rows by day and time for a logical layout
    day_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Saturday"]
    timetable_grid = timetable_grid.reset_index()
    timetable_grid['Day'] = timetable_grid['TimeSlot'].apply(lambda x: x.split(' ')[0])
    timetable_grid['Day'] = pd.Categorical(timetable_grid['Day'], categories=day_order, ordered=True)
    timetable_grid = timetable_grid.sort_values(['Day', 'TimeSlot']).drop('Day', axis=1).set_index('TimeSlot')

    # Sort columns (sections) by level (L1, L2, etc.)
    def get_level_sort_key(section_name):
        match = re.search(r"L(\d+)", section_name)
        level = int(match.group(1)) if match else 99
        section_num_str = ''.join(filter(str.isdigit, section_name.split('_')[0]))
        section_num = int(section_num_str) if section_num_str else 0
        return (level, section_num)

    sorted_columns = sorted(timetable_grid.columns, key=get_level_sort_key)
    timetable_grid = timetable_grid[sorted_columns]

    # Build the GUI Window
    window = tk.Tk()
    window.title("Generated Timetable (Arranged by Level)")
    window.geometry("1400x800")
    frame = tk.Frame(window)
    frame.pack(expand=True, fill='both')
    style = ttk.Style()
    style.configure("Treeview", rowheight=45, font=('Calibri', 9))
    style.configure("Treeview.Heading", font=('Calibri', 10, 'bold'))
    tree = ttk.Treeview(frame, style="Treeview")

    columns = ['TimeSlot'] + list(timetable_grid.columns)
    tree["columns"] = columns
    tree["show"] = "headings"

    for col in columns:
        tree.heading(col, text=col)
        width = 200 if col == 'TimeSlot' else 150
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


# --- 2. CSP FORMULATION (WITH LECTURE GROUPING) ---

def setup_csp(data):
    """
    Sets up CSP variables by grouping lectures and scheduling labs individually.
    """
    variables, domains, empty_domain_reasons = [], {}, {}
    day_to_slots = create_day_to_slots_map(data['timeslots'])

    print("\n--- Formulating CSP (Grouping Lectures) ---")
    
    instructor_prefs = {row['InstructorID']: row.get('PreferredSlots', 'Anytime') for _, row in data['instructors'].iterrows()}

    course_to_sections = {}
    for _, section in data['sections'].iterrows():
        for course_id in [c.strip() for c in str(section['Courses']).split(',') if c.strip()]:
            if course_id not in course_to_sections: course_to_sections[course_id] = []
            course_to_sections[course_id].append(section)

    for course_id, sections in course_to_sections.items():
        if course_id not in data['courses']['CourseID'].values: continue
        
        course_info = data['courses'][data['courses']['CourseID'] == course_id].iloc[0]
        course_type = course_info['Type']
        qualified_instructors = data['instructors'][data['instructors']['QualifiedCourses'].apply(lambda x: course_id in str(x))]
        
        var_types_to_create = ["Lecture", "Lab"] if course_type == "Lecture and Lab" else [course_type]

        for var_type in var_types_to_create:
            # Grouping Logic for Lectures
            if var_type == "Lecture":
                group_size = 2
                for chunk in [sections[i:i + group_size] for i in range(0, len(sections), group_size)]:
                    section_ids, total_students = [s['SectionID'] for s in chunk], sum(s['StudentCount'] for s in chunk)
                    variable = f"{course_id}_Lecture_({','.join(section_ids)})"
                    variables.append(variable)
                    
                    possible_rooms = data['rooms'][(data['rooms']['Type'] == 'Lecture') & (data['rooms']['Capacity'] >= total_students)]
                    possible_inst = qualified_instructors[qualified_instructors['InstructorID'].str.startswith('PROF')]
                    
                    initial_domain = list(product(data['timeslots']['TimeSlotID'], possible_rooms['RoomID'], possible_inst['InstructorID'])) if not possible_rooms.empty and not possible_inst.empty else []
                    domains[variable] = [(t, r, i) for t, r, i in initial_domain if not ("Not on" in str(instructor_prefs.get(i)) and t in day_to_slots.get(str(instructor_prefs.get(i)).split("Not on ")[-1].strip(), []))]
                    
                    if not domains[variable]:
                        reason = "No valid combination for this combined lecture."
                        print(f"  -> 🔴 WARNING for [{variable}]: Domain is empty. Reason: {reason}")
                        empty_domain_reasons[variable] = reason
            
            # Individual Logic for Labs
            elif var_type == "Lab":
                for section in sections:
                    variable = f"{course_id}_Lab_{section['SectionID']}"
                    variables.append(variable)
                    
                    possible_rooms = data['rooms'][(data['rooms']['Type'] == 'Lab') & (data['rooms']['Capacity'] >= section['StudentCount'])]
                    possible_inst = qualified_instructors[qualified_instructors['InstructorID'].str.startswith('AP')]
                    
                    initial_domain = list(product(data['timeslots']['TimeSlotID'], possible_rooms['RoomID'], possible_inst['InstructorID'])) if not possible_rooms.empty and not possible_inst.empty else []
                    domains[variable] = [(t, r, i) for t, r, i in initial_domain if not ("Not on" in str(instructor_prefs.get(i)) and t in day_to_slots.get(str(instructor_prefs.get(i)).split("Not on ")[-1].strip(), []))]

                    if not domains[variable]:
                        reason = "No valid combination for this individual lab."
                        print(f"  -> 🔴 WARNING for [{variable}]: Domain is empty. Reason: {reason}")
                        empty_domain_reasons[variable] = reason
                        
    print(" -> Done.")
    constraints = [(v1, v2) for i, v1 in enumerate(variables) for v2 in variables[i+1:]]
    return variables, domains, constraints, empty_domain_reasons

# --- 3. ARC CONSISTENCY ---
def get_sections_from_var(variable_name):
    """Extracts a set of individual section IDs from a (potentially grouped) variable name."""
    try:
        grouped_part = variable_name[variable_name.find('(')+1 : variable_name.find(')')]
        if grouped_part: return set(grouped_part.split(','))
        return set(['_'.join(variable_name.split('_')[2:])])
    except:
        return set()

def is_consistent(var1_assignment, var2_assignment, var1, var2):
    time1, room1, instructor1 = var1_assignment
    time2, room2, instructor2 = var2_assignment
    if time1 == time2 and (instructor1 == instructor2 or room1 == room2): return False
    
    sections1, sections2 = get_sections_from_var(var1), get_sections_from_var(var2)
    return False if time1 == time2 and not sections1.isdisjoint(sections2) else True

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
            for neighbor in [c[0] for c in constraints if c[1] == var1] + [c[1] for c in constraints if c[0] == var1]:
                if neighbor != var2:
                    queue.append((neighbor, var1))
    return True

# --- 4. BACKTRACKING SOLVER ---
def select_unassigned_variable_mrv(variables, schedule, domains):
    unassigned = [v for v in variables if v not in schedule]
    return min(unassigned, key=lambda var: len(domains[var])) if unassigned else None

def solve_backtracking(variables, domains, schedule):
    if len(schedule) == len(variables): return schedule
    variable = select_unassigned_variable_mrv(variables, schedule, domains)
    if variable is None: return None
    
    print(f" -> Solving for: {variable} ({len(schedule) + 1}/{len(variables)})")
    
    for value in domains[variable]:
        if all(is_consistent(value, val, variable, var) for var, val in schedule.items()):
            schedule[variable] = value
            result = solve_backtracking(variables, domains, schedule)
            if result: return result
            del schedule[variable]
            
    return None

# --- 5. DISPLAY AND SAVE TIMETABLE ---
def display_and_save_timetable(schedule, data, output_filename="timetable_output.csv"):
    if not schedule:
        print("\n❌ No feasible timetable could be found.")
        return

    # "Un-group" the schedule data to create a simple list of events for the GUI
    timetable_data = []
    for variable, (time_id, room_id, instructor_id) in schedule.items():
        parts = variable.split('_')
        course_id, var_type = parts[0], parts[1]
        
        sections = get_sections_from_var(variable)
        
        for section_id in sections:
            time_details = data['timeslots'].loc[data['timeslots']['TimeSlotID'] == time_id].iloc[0]
            instructor_name = data['instructors'].loc[data['instructors']['InstructorID'] == instructor_id, 'Name'].iloc[0]
            time_str = f"{time_details.get('StartTime', '')} - {time_details.get('EndTime', '')}"
            display_course = f"{course_id} ({var_type})"
            
            timetable_data.append({'Day': time_details['Day'], 'Time': time_str, 'Section': section_id, 'Course': display_course, 'Instructor': instructor_name})
    
    final_df = pd.DataFrame(timetable_data)
    
    print("\n✅ Feasible Timetable Generated Successfully!\n")
    print(final_df.sort_values(by=['Day', 'Time', 'Section']).to_string(index=False))
    
    try:
        final_df.to_csv(output_filename, index=False)
        print(f"\n✅ Timetable has been saved to '{output_filename}'")
    except Exception as e:
        print(f"\n❌ Could not save the file. Error: {e}")
        
    print("\n -> Launching GUI window...")
    display_timetable_grid_gui(final_df)


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    csv_folder_path = r"E:\CSP_data"
    dataset = load_data_from_csv(csv_folder_path)
    if dataset:
        csp_vars, csp_domains, csp_constraints, empty_reasons = setup_csp(dataset)
        
        if any(not d for d in csp_domains.values()):
             print(" -> Halting process because one or more domains are empty.")
        elif ac3(csp_vars, csp_domains, csp_constraints):
            print(" -> AC-3 successful. Domains have been pruned.")
            print("\n--- 3. Starting Solver (Backtracking + MRV) ---")
            final_schedule = solve_backtracking(csp_vars, csp_domains, {})
            display_and_save_timetable(final_schedule, dataset)
        else:
            print("❌ No solution possible. AC-3 found an inconsistency after initial setup.")
#
# Intelligent Systems Project 1:
# Final version with lecture grouping and a filterable GUI.
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

# --- GLOBAL METADATA CACHE ---
# Stores pre-computed info for variables to avoid repetitive parsing
# Structure: { variable_name: {'sections': set(...), 'type': 'Lecture'/'Lab'} }
VAR_METADATA = {}

# --- HELPER & GUI FUNCTIONS ---

def create_day_to_slots_map(timeslots_df):
    """Creates a dictionary mapping each day to a list of its TimeSlotIDs."""
    return timeslots_df.groupby('Day')['TimeSlotID'].apply(list).to_dict()

def display_timetable_grid_gui(full_schedule_df):
    """
    Creates a modern, colorful, filterable GUI window with the timetable in a grid format.
    """
    if full_schedule_df is None or full_schedule_df.empty:
        print(" -> No schedule to display in GUI.")
        return

    # --- Modern Color Scheme ---
    COLORS = {
        'bg_primary': '#1e1e2e',      # Dark background
        'bg_secondary': '#2d2d44',    # Slightly lighter dark
        'bg_tertiary': '#3a3a5c',     # Even lighter for cards
        'accent_primary': '#6c5ce7',   # Purple accent
        'accent_secondary': '#00d2d3', # Cyan accent
        'accent_success': '#00b894',  # Green
        'accent_warning': '#fdcb6e',  # Yellow
        'text_primary': '#ffffff',     # White text
        'text_secondary': '#b2bec3',  # Light gray text
        'lecture': '#a29bfe',          # Purple for lectures
        'lab': '#00d2d3',              # Cyan for labs
        'header': '#6c5ce7',           # Purple header
    }

    # --- GUI Setup ---
    window = tk.Tk()
    window.title("📅 Modern Timetable Viewer")
    window.geometry("1600x950")
    window.configure(bg=COLORS['bg_primary'])

    # --- Modern Header ---
    header_frame = tk.Frame(window, bg=COLORS['header'], height=80)
    header_frame.pack(fill='x', padx=0, pady=0)
    header_frame.pack_propagate(False)
    
    title_label = tk.Label(
        header_frame, 
        text="📅 Timetable Schedule Viewer", 
        font=('Segoe UI', 24, 'bold'),
        bg=COLORS['header'],
        fg=COLORS['text_primary']
    )
    title_label.pack(pady=20)

    # --- Top frame for controls with modern styling ---
    control_frame = tk.Frame(window, bg=COLORS['bg_secondary'], relief='flat')
    control_frame.pack(pady=15, padx=20, fill='x')

    # Inner frame for better spacing
    inner_control = tk.Frame(control_frame, bg=COLORS['bg_secondary'])
    inner_control.pack(pady=15, padx=20)

    filter_label = tk.Label(
        inner_control, 
        text="🔍 Filter by Section:", 
        font=('Segoe UI', 11, 'bold'),
        bg=COLORS['bg_secondary'],
        fg=COLORS['text_primary']
    )
    filter_label.pack(side=tk.LEFT, padx=10)

    # Get unique sections sorted by level for the dropdown
    def get_level_sort_key(section_name):
        match = re.search(r"L(\d+)", section_name)
        level = int(match.group(1)) if match else 99
        section_num_str = ''.join(filter(str.isdigit, section_name.split('_')[0]))
        section_num = int(section_num_str) if section_num_str else 0
        return (level, section_num)
    
    unique_sections = sorted(full_schedule_df['Section'].unique(), key=get_level_sort_key)
    
    section_var = tk.StringVar()
    
    # Modern styled combobox
    style = ttk.Style()
    style.theme_use('clam')
    
    # Configure modern styles
    style.configure('Modern.TCombobox', 
                    fieldbackground=COLORS['bg_tertiary'],
                    background=COLORS['bg_tertiary'],
                    foreground=COLORS['text_primary'],
                    borderwidth=0,
                    relief='flat',
                    padding=5)
    style.map('Modern.TCombobox',
              fieldbackground=[('readonly', COLORS['bg_tertiary'])],
              selectbackground=[('readonly', COLORS['accent_primary'])],
              selectforeground=[('readonly', COLORS['text_primary'])])
    
    section_dropdown = ttk.Combobox(
        inner_control, 
        textvariable=section_var, 
        values=unique_sections, 
        state='readonly', 
        width=28,
        style='Modern.TCombobox',
        font=('Segoe UI', 10)
    )
    section_dropdown.pack(side=tk.LEFT, padx=10)

    # --- Treeview frame with modern container ---
    container_frame = tk.Frame(window, bg=COLORS['bg_primary'])
    container_frame.pack(expand=True, fill='both', padx=20, pady=(0, 20))

    tree_frame = tk.Frame(container_frame, bg=COLORS['bg_secondary'], relief='flat')
    tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

    # Configure modern Treeview styles
    style.configure("Modern.Treeview",
                    background=COLORS['bg_tertiary'],
                    foreground=COLORS['text_primary'],
                    fieldbackground=COLORS['bg_tertiary'],
                    rowheight=75,
                    font=('Segoe UI', 11))
    style.configure("Modern.Treeview.Heading",
                    background=COLORS['accent_primary'],
                    foreground=COLORS['text_primary'],
                    font=('Segoe UI', 11, 'bold'),
                    relief='flat',
                    borderwidth=0)
    style.map("Modern.Treeview",
              background=[('selected', COLORS['accent_primary'])],
              foreground=[('selected', COLORS['text_primary'])])
    
    tree = ttk.Treeview(tree_frame, style="Modern.Treeview")

    # Modern scrollbars
    style.configure("Modern.Vertical.TScrollbar",
                    background=COLORS['bg_tertiary'],
                    troughcolor=COLORS['bg_secondary'],
                    borderwidth=0,
                    arrowcolor=COLORS['text_primary'],
                    darkcolor=COLORS['bg_tertiary'],
                    lightcolor=COLORS['bg_tertiary'])
    style.configure("Modern.Horizontal.TScrollbar",
                    background=COLORS['bg_tertiary'],
                    troughcolor=COLORS['bg_secondary'],
                    borderwidth=0,
                    arrowcolor=COLORS['text_primary'],
                    darkcolor=COLORS['bg_tertiary'],
                    lightcolor=COLORS['bg_tertiary'])

    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview, style="Modern.Vertical.TScrollbar")
    hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview, style="Modern.Horizontal.TScrollbar")
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tree.pack(side="left", expand=True, fill="both")

    # --- Helper function to format cell content with emojis ---
    def format_cell_content(cell_content):
        if not cell_content or cell_content == '':
            return ''
        content_str = str(cell_content)
        if '\n' in content_str:
            parts = content_str.split('\n')
            course_part = parts[0].strip() if len(parts) > 0 else ''
            instructor_part = parts[1].strip() if len(parts) > 1 else ''
            
            if '(Lecture)' in course_part:
                course_name = course_part.replace('(Lecture)', '').strip()
                return f'📚 {course_name}\n👨‍🏫 {instructor_part}' if instructor_part else f'📚 {course_name}'
            elif '(Lab)' in course_part:
                course_name = course_part.replace('(Lab)', '').strip()
                return f'🔬 {course_name}\n👨‍🔬 {instructor_part}' if instructor_part else f'🔬 {course_name}'
            else:
                return f'{course_part}\n👤 {instructor_part}' if instructor_part else course_part
        else:
            # No newline, just course name
            if '(Lecture)' in content_str:
                course_name = content_str.replace('(Lecture)', '').strip()
                return f'📚 {course_name}'
            elif '(Lab)' in content_str:
                course_name = content_str.replace('(Lab)', '').strip()
                return f'🔬 {course_name}'
            return content_str

    # --- Helper function to get row tag based on content ---
    def get_row_tag(row_values):
        """Determine if row has lectures, labs, or mixed content for coloring"""
        has_lecture = any('(Lecture)' in str(v) for v in row_values)
        has_lab = any('(Lab)' in str(v) for v in row_values)
        if has_lecture and not has_lab:
            return 'lecture_row'
        elif has_lab and not has_lecture:
            return 'lab_row'
        elif has_lecture and has_lab:
            return 'mixed_row'
        return 'empty_row'

    # --- Helper function to populate the Treeview ---
    def populate_tree(schedule_df):
        # Clear existing Treeview content
        for item in tree.get_children():
            tree.delete(item)
        for col in tree["columns"]:
            tree.heading(col, text="")
        tree["columns"] = []

        if schedule_df is None or schedule_df.empty:
            return

        # Prepare data (avoid unnecessary copy if possible)
        schedule_df = schedule_df.copy()
        schedule_df['TimeSlot'] = schedule_df['Day'] + " " + schedule_df['Time']
        schedule_df['CellContent'] = schedule_df['Course'] + "\n" + schedule_df['Instructor']

        timetable_grid = schedule_df.pivot_table(
            index='TimeSlot', columns='Section', values='CellContent', aggfunc='first'
        ).fillna('')

        # Sort rows - use vectorized operations
        day_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Saturday"]
        timetable_grid = timetable_grid.reset_index()
        # Vectorized day extraction
        timetable_grid['Day'] = timetable_grid['TimeSlot'].str.split(' ', n=1).str[0]
        timetable_grid['Day'] = pd.Categorical(timetable_grid['Day'], categories=day_order, ordered=True)
        timetable_grid = timetable_grid.sort_values(['Day', 'TimeSlot']).drop('Day', axis=1).set_index('TimeSlot')

        # Sort columns (if more than one section is displayed)
        if len(timetable_grid.columns) > 1:
            sorted_columns = sorted(timetable_grid.columns, key=get_level_sort_key)
            timetable_grid = timetable_grid[sorted_columns]

        # Define Treeview columns and headings
        columns = ['TimeSlot'] + list(timetable_grid.columns)
        tree["columns"] = columns
        tree["show"] = "headings"

        for col in columns:
            tree.heading(col, text=col)
            width = 280 if col == 'TimeSlot' else 220
            tree.column(col, anchor="center", width=width, stretch=False)

        # Configure row tags with colors
        tree.tag_configure('lecture_row', background='#2d2d44')
        tree.tag_configure('lab_row', background='#1e3a3a')
        tree.tag_configure('mixed_row', background='#3a2d3a')
        tree.tag_configure('empty_row', background=COLORS['bg_tertiary'])
        tree.tag_configure('even_row', background='#2a2a3a')
        tree.tag_configure('odd_row', background='#252535')

        # Day emoji mapping
        day_emojis = {
            'Sunday': '☀️',
            'Monday': '📅',
            'Tuesday': '📆',
            'Wednesday': '🗓️',
            'Thursday': '📋',
            'Saturday': '🎯'
        }
        
        # Pre-compute formatted values using itertuples (much faster than iterrows)
        rows_to_insert = []
        row_values_list = timetable_grid.values.tolist()
        row_index_list = timetable_grid.index.tolist()
        
        for row_idx, (index, row_values) in enumerate(zip(row_index_list, row_values_list)):
            # Format TimeSlot with day emoji
            day_name = index.split(' ')[0] if ' ' in index else index
            emoji = day_emojis.get(day_name, '⏰')
            formatted_timeslot = f"{emoji} {index}"
            
            # Format cell contents with emojis
            formatted_values = [formatted_timeslot]
            formatted_values.extend(format_cell_content(val) for val in row_values)
            
            # Determine row tag based on content
            row_tag = get_row_tag(row_values)
            alt_tag = 'even_row' if row_idx % 2 == 0 else 'odd_row'
            
            rows_to_insert.append((formatted_values, (row_tag, alt_tag)))
        
        # Batch insert (faster than individual inserts)
        for formatted_values, tags in rows_to_insert:
            tree.insert("", tk.END, values=formatted_values, tags=tags)

    # --- Filter and Reset Logic ---
    def filter_view():
        selected_section = section_var.get()
        if selected_section:
            filtered_df = full_schedule_df[full_schedule_df['Section'] == selected_section].copy()
            populate_tree(filtered_df)
        else:
            populate_tree(full_schedule_df)

    def reset_view():
        section_dropdown.set('')
        populate_tree(full_schedule_df)

    # --- Modern styled buttons ---
    style.configure('Modern.TButton',
                    background=COLORS['accent_primary'],
                    foreground=COLORS['text_primary'],
                    borderwidth=0,
                    relief='flat',
                    padding=10,
                    font=('Segoe UI', 10, 'bold'))
    style.map('Modern.TButton',
              background=[('active', COLORS['accent_secondary']),
                         ('pressed', COLORS['accent_primary'])],
              foreground=[('active', COLORS['text_primary'])])

    style.configure('Reset.TButton',
                    background=COLORS['accent_success'],
                    foreground=COLORS['text_primary'],
                    borderwidth=0,
                    relief='flat',
                    padding=10,
                    font=('Segoe UI', 10, 'bold'))
    style.map('Reset.TButton',
              background=[('active', '#00a085'),
                         ('pressed', COLORS['accent_success'])],
              foreground=[('active', COLORS['text_primary'])])

    filter_button = ttk.Button(inner_control, text="🔍 Filter", command=filter_view, style='Modern.TButton')
    filter_button.pack(side=tk.LEFT, padx=10)

    reset_button = ttk.Button(inner_control, text="🔄 Show All", command=reset_view, style='Reset.TButton')
    reset_button.pack(side=tk.LEFT, padx=10)

    # --- Legend frame ---
    legend_frame = tk.Frame(inner_control, bg=COLORS['bg_secondary'])
    legend_frame.pack(side=tk.LEFT, padx=20)
    
    legend_label = tk.Label(
        legend_frame,
        text="Legend:",
        font=('Segoe UI', 9, 'bold'),
        bg=COLORS['bg_secondary'],
        fg=COLORS['text_secondary']
    )
    legend_label.pack(side=tk.LEFT, padx=5)
    
    lecture_legend = tk.Label(
        legend_frame,
        text="📚 Lecture",
        font=('Segoe UI', 9),
        bg=COLORS['lecture'],
        fg=COLORS['text_primary'],
        padx=8,
        pady=2,
        relief='flat'
    )
    lecture_legend.pack(side=tk.LEFT, padx=5)
    
    lab_legend = tk.Label(
        legend_frame,
        text="🔬 Lab",
        font=('Segoe UI', 9),
        bg=COLORS['lab'],
        fg=COLORS['bg_primary'],
        padx=8,
        pady=2,
        relief='flat'
    )
    lab_legend.pack(side=tk.LEFT, padx=5)

    # --- Initial population ---
    populate_tree(full_schedule_df)

    window.mainloop()


# --- 2. CSP FORMULATION (WITH LECTURE GROUPING) ---

def setup_csp(data):
    """
    Sets up CSP variables by grouping lectures and scheduling labs individually.
    Optimized version with pre-computed mappings and efficient domain generation.
    """
    global VAR_METADATA
    VAR_METADATA.clear() # Reset cache
    
    variables, domains, empty_domain_reasons = [], {}, {}
    day_to_slots = create_day_to_slots_map(data['timeslots'])

    print("\n--- Formulating CSP (Grouping Lectures) ---")
    
    # Pre-compute instructor preferences and forbidden days for faster lookup
    instructor_prefs = {}
    instructor_forbidden_days = {}  # Cache forbidden days per instructor
    for _, row in data['instructors'].iterrows():
        inst_id = row['InstructorID']
        pref = row.get('PreferredSlots', 'Anytime')
        instructor_prefs[inst_id] = pref
        if "Not on" in str(pref):
            forbidden_day = str(pref).split("Not on ")[-1].strip()
            instructor_forbidden_days[inst_id] = set(day_to_slots.get(forbidden_day, []))
        else:
            instructor_forbidden_days[inst_id] = set()
    
    # Pre-compute qualified instructors per course (much faster than repeated filtering)
    course_to_qualified_instructors = {}
    instructors_df = data['instructors']
    for course_id in data['courses']['CourseID'].unique():
        # Use vectorized string operations instead of apply
        mask = instructors_df['QualifiedCourses'].astype(str).str.contains(course_id, na=False)
        course_to_qualified_instructors[course_id] = instructors_df[mask]

    # Pre-compute room lists by type and capacity ranges
    lecture_rooms = data['rooms'][data['rooms']['Type'] == 'Lecture'].copy()
    lab_rooms = data['rooms'][data['rooms']['Type'] == 'Lab'].copy()
    timeslot_ids = data['timeslots']['TimeSlotID'].tolist()

    course_to_sections = {}
    for _, section in data['sections'].iterrows():
        for course_id in [c.strip() for c in str(section['Courses']).split(',') if c.strip()]:
            if course_id not in course_to_sections: course_to_sections[course_id] = []
            course_to_sections[course_id].append(section)

    for course_id, sections in course_to_sections.items():
        if course_id not in data['courses']['CourseID'].values: continue
        
        course_info = data['courses'][data['courses']['CourseID'] == course_id].iloc[0]
        course_type = course_info['Type']
        qualified_instructors = course_to_qualified_instructors.get(course_id, pd.DataFrame())
        
        var_types_to_create = ["Lecture", "Lab"] if course_type == "Lecture and Lab" else [course_type]

        for var_type in var_types_to_create:
            # Grouping Logic for Lectures
            if var_type == "Lecture":
                group_size = 2 
                for chunk in [sections[i:i + group_size] for i in range(0, len(sections), group_size)]:
                    section_ids, total_students = [s['SectionID'] for s in chunk], sum(s['StudentCount'] for s in chunk)
                    variable = f"{course_id}_Lecture_({','.join(section_ids)})"
                    variables.append(variable)
                    
                    # Cache metadata
                    VAR_METADATA[variable] = {'sections': set(section_ids)}

                    # Filter rooms by capacity (vectorized)
                    possible_rooms = lecture_rooms[lecture_rooms['Capacity'] >= total_students]
                    possible_inst = qualified_instructors[qualified_instructors['InstructorID'].str.startswith('PROF')]
                    
                    if possible_rooms.empty or possible_inst.empty:
                        domains[variable] = []
                    else:
                        # Optimized domain generation: List comprehension to avoid generating full product first
                        room_ids = possible_rooms['RoomID'].values
                        inst_ids = possible_inst['InstructorID'].values
                        
                        domains[variable] = [
                            (t, r, i)
                            for t in timeslot_ids
                            for r in room_ids
                            for i in inst_ids
                            if t not in instructor_forbidden_days.get(i, set())
                        ]
                    
                    if not domains[variable]:
                        reason = "No valid combination for this combined lecture."
                        print(f"  -> 🔴 WARNING for [{variable}]: Domain is empty. Reason: {reason}")
                        empty_domain_reasons[variable] = reason
            
            # Individual Logic for Labs
            elif var_type == "Lab":
                for section in sections:
                    variable = f"{course_id}_Lab_{section['SectionID']}"
                    variables.append(variable)
                    
                    # Cache metadata
                    VAR_METADATA[variable] = {'sections': {section['SectionID']}}

                    # Filter rooms by capacity (vectorized)
                    possible_rooms = lab_rooms[lab_rooms['Capacity'] >= section['StudentCount']]
                    possible_inst = qualified_instructors[qualified_instructors['InstructorID'].str.startswith('AP')]
                    
                    if possible_rooms.empty or possible_inst.empty:
                        domains[variable] = []
                    else:
                        # Optimized domain generation
                        room_ids = possible_rooms['RoomID'].values
                        inst_ids = possible_inst['InstructorID'].values
                        
                        domains[variable] = [
                            (t, r, i)
                            for t in timeslot_ids
                            for r in room_ids
                            for i in inst_ids
                            if t not in instructor_forbidden_days.get(i, set())
                        ]

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
        start_paren = variable_name.find('(')
        end_paren = variable_name.find(')')

        # --- CORRECTED CHECK ---
        # Only treat as grouped if BOTH parentheses are present
        if start_paren != -1 and end_paren != -1 and start_paren < end_paren:
            grouped_part = variable_name[start_paren + 1 : end_paren]
            return set(grouped_part.split(','))
        else:
            # Handle individual variable format (the original fallback logic)
            parts = variable_name.split('_')
            if len(parts) >= 3:
                 # Assume section ID starts from the 3rd part onwards
                 return set(['_'.join(parts[2:])])
            else:
                 print(f"Warning: Unexpected variable format '{variable_name}'")
                 return set()
    except Exception as e:
         print(f"Error parsing variable '{variable_name}': {e}")
         return set()


def is_consistent(var1_assignment, var2_assignment, var1, var2):
    time1, room1, instructor1 = var1_assignment
    time2, room2, instructor2 = var2_assignment
    
    # Conflict 1: Time overlap + (Same Instructor OR Same Room)
    if time1 == time2 and (instructor1 == instructor2 or room1 == room2): 
        return False
    
    # Conflict 2: Time overlap + Overlapping Student Sections
    # Optimized: Use pre-computed metadata from setup_csp
    if time1 == time2:
        # Use simple dictionary lookup - O(1)
        sections1 = VAR_METADATA.get(var1, {}).get('sections')
        sections2 = VAR_METADATA.get(var2, {}).get('sections')
        
        # If metadata missing (fallback safety), use slow parsing
        if sections1 is None: sections1 = get_sections_from_var(var1)
        if sections2 is None: sections2 = get_sections_from_var(var2)
        
        if sections1 and sections2:
             if not sections1.isdisjoint(sections2):
                 return False
                 
    return True


def revise(domains, var1, var2):
    """
    Revise function - keeps values from var1 that are consistent with at least one value in var2.
    Uses list comprehension which is optimized by Python.
    """
    initial_size = len(domains[var1])
    # Use list comprehension with any() for early termination (Python optimizes this)
    domains[var1] = [val1 for val1 in domains[var1] 
                     if any(is_consistent(val1, val2, var1, var2) for val2 in domains[var2])]
    return len(domains[var1]) < initial_size


def ac3(variables, domains, constraints):
    queue = deque(constraints + [(v2, v1) for v1, v2 in constraints])
    # Build neighbor map for faster lookups
    neighbors = {v: [] for v in variables}
    for v1, v2 in constraints:
        neighbors[v1].append(v2)
        neighbors[v2].append(v1)
        
    while queue:
        var1, var2 = queue.popleft()
        if revise(domains, var1, var2):
            if not domains[var1]: return False
            # Only add neighbors of var1 (excluding var2) back to the queue
            for neighbor in neighbors[var1]:
                if neighbor != var2:
                    queue.append((neighbor, var1))
    return True


# --- 4. BACKTRACKING SOLVER ---
def select_unassigned_variable_mrv(variables, schedule, domains):
    unassigned = [v for v in variables if v not in schedule]
    # Add a tie-breaker (e.g., degree heuristic) if needed, but simple min is usually fine
    return min(unassigned, key=lambda var: len(domains[var])) if unassigned else None

def solve_backtracking(variables, domains, schedule):
    """
    Backtracking solver with MRV heuristic.
    Simplified version for better performance - checks all assigned variables.
    """
    if len(schedule) == len(variables): return schedule
    variable = select_unassigned_variable_mrv(variables, schedule, domains)
    if variable is None: return None
    
    print(f" -> Solving for: {variable} ({len(schedule) + 1}/{len(variables)})") # Optional progress print
    
    # Try values in their current order
    for value in domains[variable]:
        # Check consistency against all assigned variables
        is_assignment_consistent = True
        for assigned_var, assigned_value in schedule.items():
            if not is_consistent(value, assigned_value, variable, assigned_var):
                is_assignment_consistent = False
                break
        
        if is_assignment_consistent:
            schedule[variable] = value
            result = solve_backtracking(variables, domains, schedule)
            if result: return result
            del schedule[variable] # Backtrack
            
    return None


# --- 5. DISPLAY AND SAVE TIMETABLE ---
def display_and_save_timetable(schedule, data, output_filename="timetable_output.csv"):
    if not schedule:
        print("\n❌ No feasible timetable could be found.")
        return

    # Create lookup dictionaries for O(1) access instead of O(n) DataFrame filtering
    # Use to_dict('index') for faster conversion (more efficient than iterrows)
    timeslots_dict = data['timeslots'].set_index('TimeSlotID').to_dict('index')
    instructors_dict = data['instructors'].set_index('InstructorID').to_dict('index')

    timetable_data = []
    for variable, (time_id, room_id, instructor_id) in schedule.items():
        parts = variable.split('_')
        course_id, var_type = parts[0], parts[1]
        
        sections = get_sections_from_var(variable)
        if not sections: # Skip if section parsing failed
             print(f"Warning: Skipping variable '{variable}' in output due to section parsing error.")
             continue

        # Fast dictionary lookups instead of DataFrame filtering
        time_details = timeslots_dict.get(time_id)
        instructor_info = instructors_dict.get(instructor_id)
        
        if time_details is None or instructor_info is None:
            print(f"Warning: Missing data for TimeSlot '{time_id}' or Instructor '{instructor_id}'. Skipping entry.")
            continue
        
        instructor_name = instructor_info.get('Name', 'N/A')
        time_str = f"{time_details.get('StartTime', 'N/A')} - {time_details.get('EndTime', 'N/A')}"
        display_course = f"{course_id} ({var_type})"
        
        for section_id in sections:
            timetable_data.append({
                'Day': time_details.get('Day', 'N/A'),
                'Time': time_str,
                'Section': section_id,
                'Course': display_course,
                'Instructor': instructor_name
            })
    
    if not timetable_data:
        print("\n❌ No timetable data generated after processing schedule.")
        return
        
    final_df = pd.DataFrame(timetable_data)
    
    print("\n✅ Feasible Timetable Generated Successfully!\n")
    # Ensure sorting columns exist before sorting
    sort_cols = [col for col in ['Day', 'Time', 'Section'] if col in final_df.columns]
    if sort_cols:
        print(final_df.sort_values(by=sort_cols).to_string(index=False))
    else:
        print(final_df.to_string(index=False)) # Print unsorted if columns missing
    
    try:
        final_df.to_csv(output_filename, index=False)
        print(f"\n✅ Timetable has been saved to '{output_filename}'")
    except Exception as e:
        print(f"\n❌ Could not save the file. Error: {e}")
        
    print("\n -> Launching GUI window...")
    display_timetable_grid_gui(final_df)

def save_extracted_sections_to_file(variables, filename="extracted_sections_output.txt"):
    """
    Runs get_sections_from_var on all variables and saves the results to a file.
    Uses the provided get_sections_from_var function.
    """
    print(f"\n -> Extracting section IDs for {len(variables)} variables...")
    try:
        with open(filename, 'w') as f:
            f.write("--- Extracted Section IDs from CSP Variables ---\n\n")
            for var in sorted(variables):
                # Call the existing function to get the section IDs
                extracted_sections = get_sections_from_var(var)

                # Format the output line
                sections_str = ', '.join(sorted(list(extracted_sections))) if extracted_sections else '{}'
                output_line = f"Variable: {var}  ->  Sections: {{{sections_str}}}\n"
                f.write(output_line)

        print(f"✅ Extracted section IDs saved to '{filename}'")
    except Exception as e:
        print(f"\n❌ Could not save the extracted sections file. Error: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Robust path handling
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
    csv_folder_path = r"E:\CSP_data" # Assume data is in a subfolder
    # Or use the absolute path: csv_folder_path = r"E:\CSP_data"

    dataset = load_data_from_csv(csv_folder_path)
    if dataset:
        try:
            csp_vars, csp_domains, csp_constraints, empty_reasons = setup_csp(dataset)

            #save_extracted_sections_to_file(csp_vars)
            
            if any(not d for d in csp_domains.values()):
                 print(" -> Halting process because one or more domains are empty after setup.")
            elif ac3(csp_vars, csp_domains, csp_constraints): # Pass copies if AC3 modifies in place? Check AC3 impl.
                print(" -> AC-3 successful. Domains have been pruned.")
                print("\n--- 3. Starting Solver (Backtracking + MRV) ---")
                
                # Make copies of domains if solver modifies them? Check solver impl.
                solver_domains = {var: list(dom) for var, dom in csp_domains.items()}
                
                final_schedule = solve_backtracking(csp_vars, solver_domains, {}) # Pass copy of domains
                display_and_save_timetable(final_schedule, dataset)
            else:
                print("❌ No solution possible. AC-3 found an inconsistency after initial setup.")
        except Exception as e:
            print(f"\n❌ An unexpected error occurred during solving: {e}")
            import traceback
            traceback.print_exc() # Print detailed traceback for debugging
# Intelligent Timetabling System Using Constraint Satisfaction Problem (CSP)
## Project Report

---

## Table of Contents
1. [Introduction](#introduction)
2. [Methodology / System Design](#methodology--system-design)
3. [Implementation & Technical Quality](#implementation--technical-quality)
4. [Results & Evaluation](#results--evaluation)
5. [Innovation / Complexity](#innovation--complexity)
6. [Conclusion](#conclusion)
7. [References](#references)

---

## Introduction

This project presents an intelligent timetabling system that automatically generates feasible course schedules for educational institutions using Constraint Satisfaction Problem (CSP) techniques. The system addresses the complex challenge of scheduling multiple courses, sections, instructors, and rooms while satisfying various constraints such as instructor availability, room capacity, time slot conflicts, and section overlaps.

The system is designed to handle real-world academic scheduling scenarios, including courses with both lecture and lab components, multiple sections per course, instructor preferences, and room type requirements. By leveraging CSP algorithms and optimization techniques, the system efficiently generates conflict-free timetables that respect all specified constraints. Additionally, a newly implemented **Web Interface** provides broader accessibility, allowing users to interact with the system, generate timetables, and visualize results through a modern web browser.

---

## Methodology / System Design

### 2.1 Problem Formulation

The timetabling problem is formulated as a Constraint Satisfaction Problem (CSP) with the following components:

#### 2.1.1 Variables
Each variable represents a course-section combination that needs to be scheduled. The system creates two types of variables:
- **Lecture Variables**: Grouped lectures combining multiple sections (group size = 2) to optimize resource utilization
- **Lab Variables**: Individual lab sessions for each section

Variable naming convention: `{CourseID}_{Type}_{SectionID}` or `{CourseID}_{Type}_({SectionID1,SectionID2})` for grouped lectures.

#### 2.1.2 Domains
Each variable's domain consists of all possible assignments in the form of tuples: `(TimeSlotID, RoomID, InstructorID)`. Domains are pre-filtered based on:
- **Room Capacity**: Rooms must accommodate the total number of students
- **Room Type**: Lecture rooms for lectures, lab rooms for labs
- **Instructor Qualifications**: Only instructors qualified for the course
- **Instructor Type**: Professors (PROF) for lectures, Assistant Professors (AP) for labs
- **Instructor Preferences**: Forbidden days are excluded from domains

#### 2.1.3 Constraints
The system enforces the following hard constraints:
1. **Time-Room Conflict**: No two assignments can use the same room at the same time
2. **Time-Instructor Conflict**: No instructor can teach two classes simultaneously
3. **Section Overlap**: No section can have multiple classes at the same time slot
4. **Room Capacity**: Room capacity must be sufficient for student count
5. **Instructor Availability**: Instructor forbidden days are respected

### 2.2 System Architecture

The system follows a modular architecture with the following components:

```
┌─────────────────────────────────────────────────────────┐
│                    Data Loading Module                   │
│  (CSV files: Courses, Instructors, Rooms, TimeSlots)    │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  CSP Formulation Module                  │
│  • Variable Creation (with Lecture Grouping)             │
│  • Domain Generation (pre-filtered)                     │
│  • Constraint Definition                                │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Arc Consistency (AC-3) Module               │
│  • Domain Pruning                                       │
│  • Constraint Propagation                               │
│  • Early Inconsistency Detection                        │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Backtracking Solver with MRV Heuristic         │
│  • Minimum Remaining Values (MRV)                       │
│  • Forward Checking                                    │
│  • Solution Generation                                 │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Output & Visualization Module              │
│  • CSV Export                                          │
│  • Interactive GUI with Filtering                      │
│  • Building/Room Data Extraction                       │
└─────────────────────────────────────────────────────────┘
```

### 2.3 Algorithm Selection

#### 2.3.1 AC-3 Algorithm
The AC-3 (Arc Consistency 3) algorithm is used for constraint propagation and domain pruning. This preprocessing step significantly reduces the search space before backtracking, improving overall efficiency.

**Algorithm Steps:**
1. Initialize queue with all constraint arcs (bidirectional)
2. While queue is not empty:
   - Remove arc (Xi, Xj) from queue
   - Revise domain of Xi based on Xj
   - If domain changed, add all arcs (Xk, Xi) where k ≠ j
3. Return True if all domains remain non-empty, False otherwise

#### 2.3.2 Backtracking with MRV
The backtracking solver uses the Minimum Remaining Values (MRV) heuristic to select the next variable to assign. This heuristic chooses the variable with the smallest domain, leading to early failure detection and reduced search time.

**Algorithm Steps:**
1. If all variables assigned, return solution
2. Select unassigned variable using MRV heuristic
3. For each value in variable's domain:
   - Check consistency with all assigned variables
   - If consistent, assign and recursively solve
   - If solution found, return it
   - Otherwise, backtrack (remove assignment)
4. Return None if no solution exists

### 2.4 Lecture Grouping Strategy

A key innovation in the system is the **lecture grouping strategy**. Instead of scheduling each section's lecture separately, the system groups multiple sections (default: 2) into combined lecture sessions. This approach:

- **Reduces Variables**: Fewer CSP variables to solve
- **Optimizes Resources**: Better utilization of large lecture halls
- **Maintains Flexibility**: Labs remain individual for practical requirements
- **Improves Efficiency**: Smaller search space leads to faster solutions

The grouping is implemented by:
1. Identifying all sections for a course
2. Partitioning sections into groups of size 2
3. Creating a single variable per group with combined student count
4. Maintaining individual lab variables for each section

### 2.5 Web Interface Architecture

The system extends its core consistency by offering a modern web-based user interface, built on a client-server architecture:

- **Frontend (Client)**: Developed using **React.js** (via Vite), this layer provides an interactive dashboard for users. It handles state management, user inputs (filters), and renders the generated timetable in an intuitive grid layout.
- **Backend (Server)**: Built with **Flask**, this layer acts as the bridge between the Core CSP Logic and the Frontend. It exposes API endpoints (e.g., `/api/solve`) to trigger the solving process and return results in JSON format.

---

## Implementation & Technical Quality

### 3.1 Programming Language and Libraries

The system is implemented in **Python 3** using the following libraries:
- **pandas**: Data manipulation and CSV handling
- **tkinter**: GUI development for timetable visualization
- **itertools**: Efficient Cartesian product generation for domains
- **collections.deque**: Efficient queue implementation for AC-3

### 3.2 Code Quality and Optimization

#### 3.2.1 Performance Optimizations

1. **Pre-computation and Caching**:
   - Instructor preferences and forbidden days are pre-computed and stored in dictionaries
   - Qualified instructors per course are cached to avoid repeated filtering
   - Room lists by type are pre-filtered once

2. **Vectorized Operations**:
   - Pandas vectorized string operations instead of row-by-row iteration
   - Efficient DataFrame filtering using boolean masks
   - Dictionary lookups (O(1)) instead of DataFrame filtering (O(n))

3. **Efficient Data Structures**:
   - Dictionary-based lookups for O(1) access to timeslots and instructors
   - Set operations for fast section overlap detection
   - Deque for efficient queue operations in AC-3

4. **Domain Generation Optimization**:
   - Uses `itertools.product()` for efficient Cartesian product generation
   - Pre-filters domains using set operations for forbidden days
   - Early termination in consistency checks

#### 3.2.2 Code Organization

The code is organized into clear, modular functions:

- **Data Loading**: `load_data_from_csv()` - Robust error handling and data validation
- **CSP Setup**: `setup_csp()` - Comprehensive variable and domain generation
- **Arc Consistency**: `ac3()`, `revise()`, `is_consistent()` - Clean separation of concerns
- **Solver**: `solve_backtracking()`, `select_unassigned_variable_mrv()` - Clear algorithm implementation
- **Output**: `display_and_save_timetable()`, `display_timetable_grid_gui()` - User-friendly presentation

#### 3.2.3 Error Handling

The implementation includes comprehensive error handling:
- File not found exceptions with clear error messages
- Empty domain detection with detailed warnings
- Missing data validation before processing
- Graceful handling of parsing errors

#### 3.2.4 User Interface Quality

The GUI implementation demonstrates high technical quality:

1. **Modern Design**:
   - Dark theme with carefully chosen color palette
   - Professional typography (Segoe UI font family)
   - Consistent spacing and padding
   - Visual hierarchy with emoji indicators

2. **Functionality**:
   - Real-time filtering by section
   - Sortable columns with intelligent sorting (by level and section number)
   - Color-coded rows (lectures, labs, mixed)
   - Responsive layout with scrollbars

3. **Performance**:
   - Batch insertion for Treeview (faster than individual inserts)
   - Pre-computed formatting values
   - Efficient DataFrame operations for filtering

### 3.3 Data Processing

The system includes a separate module for extracting building and room information from Excel files:

- **Excel Parsing**: Handles complex Excel structures with forward-filling building names
- **Data Export**: Supports both JSON (structured) and CSV (tabular) formats
- **Data Validation**: Filters out invalid rows and handles missing data

### 3.4 Testing and Validation

The system includes validation checks:
- Empty domain detection before solving
- AC-3 consistency checking
- Solution verification (all constraints satisfied)
- Output data integrity checks

### 3.5 Web Application Implementation

The Web Interface is a key addition to the system's technical implementation:

#### 3.5.1 Frontend (React + Vite)
- **Component-Based Architecture**: The UI is built using reusable components (e.g., for filter controls and timetable cards).
- **State Management**: React Hooks (`useState`, `useEffect`) manage the application state, including loading statuses, error handling, and schedule data.
- **Dynamic CSS**: Styles are implemented for responsiveness and a modern "Dark Mode" aesthetic.

#### 3.5.2 Backend (Flask API)
- **API Endpoints**:
  - `GET /api/solve`: Triggers the CSP solver (running `ac3` and `solve_backtracking`), formats the output, and returns it as a JSON payload.
  - `GET /health`: A simple health check endpoint.
- **Data Flow Integration**: The backend seamlessly imports the core `cspGrouping` module to reuse the existing logic, ensuring consistency between the CLI/GUI and Web results.
- **CORS Support**: Cross-Origin Resource Sharing is enabled to allow the React frontend to communicate with the Flask server during development.

---

## Results & Evaluation

### 4.1 System Performance

The system successfully generates feasible timetables for complex academic scheduling scenarios. Based on the output analysis:

#### 4.1.1 Solution Quality

**Coverage**: The system successfully schedules:
- Multiple course levels (L1, L2, L3, L4)
- Various course types (Lecture-only, Lab-only, Lecture and Lab)
- Multiple sections per course (up to 12 sections for some courses)
- Diverse instructor assignments
- Proper room allocation based on capacity and type

**Constraint Satisfaction**: All hard constraints are satisfied:
- ✅ No time-room conflicts
- ✅ No time-instructor conflicts
- ✅ No section overlaps
- ✅ Room capacity requirements met
- ✅ Instructor preferences respected

#### 4.1.2 Example Results

From the generated timetable (`timetable_output.csv`):

- **Total Scheduled Sessions**: 341 course sessions
- **Lecture Sessions**: 195 sessions
- **Lab Sessions**: 146 sessions
- **Unique Courses**: 63 different courses
- **Sections Covered**: 41 unique sections across 4 academic levels (L1, L2, L3, L4)
- **Instructors Assigned**: 45 different instructors
- **Days Covered**: Sunday, Monday, Tuesday, Wednesday, Thursday
- **Time Distribution**: Efficient distribution across all available days
- **Resource Utilization**: Optimal use of lecture halls and lab rooms

**Sample Schedule Excerpt**:
```
Course: LRA101 (Lecture)
- Sections S1_L1, S2_L1: Sunday 9:00 AM - 10:30 AM, Dr. Sherine Elmotasem
- Sections S3_L1, S4_L1: Sunday 10:45 AM - 12:15 PM, Dr. Sherine Elmotasem
- Sections S5_L1, S6_L1: Sunday 12:30 PM - 2:00 PM, Dr. Sherine Elmotasem
- Sections S7_L1, S8_L1: Sunday 2:15 PM - 3:45 PM, Dr. Sherine Elmotasem
```

This demonstrates successful lecture grouping (2 sections per lecture) while maintaining individual lab sessions.

#### 4.1.3 Building and Room Data Extraction

The system successfully extracted building and room information:
- **20 Buildings** identified
- **122+ Rooms** catalogued with capacities and types
- **Room Types**: Classrooms, Theaters, Halls, Computer Labs, Drawing Studios
- **Capacity Range**: 15 to 150 seats

### 4.2 Algorithm Effectiveness

#### 4.2.1 AC-3 Performance

The AC-3 algorithm effectively prunes the search space:
- **Early Detection**: Identifies inconsistent problems before backtracking
- **Domain Reduction**: Significantly reduces domain sizes through constraint propagation
- **Efficiency**: O(cd³) complexity where c is number of constraints and d is domain size

#### 4.2.2 Backtracking with MRV

The MRV heuristic improves search efficiency:
- **Fail-Fast**: Detects inconsistencies early by choosing constrained variables first
- **Reduced Backtracking**: Smaller domains lead to fewer dead ends
- **Solution Quality**: Maintains completeness while improving efficiency

### 4.3 User Experience

#### 4.3.1 GUI Evaluation

The interactive GUI provides:
- **Intuitive Navigation**: Easy filtering and reset functionality
- **Visual Clarity**: Color-coded course types and organized layout
- **Information Density**: Comprehensive timetable view with all relevant details
- **Responsiveness**: Fast filtering and display updates

#### 4.3.2 Output Formats

Multiple output formats enhance usability:
- **CSV Export**: Easy integration with other systems
- **Interactive GUI**: Real-time exploration and filtering
- **JSON/CSV Building Data**: Structured data for further analysis

### 4.4 Limitations and Challenges

1. **Scalability**: Very large problems (100+ variables) may require additional optimizations
2. **Soft Constraints**: Currently only hard constraints are enforced; soft constraints (preferences) could be added
3. **Multi-objective Optimization**: Could be extended to optimize for multiple objectives (e.g., minimize gaps, maximize room utilization)

---

## Innovation / Complexity

### 5.1 Innovative Features

#### 5.1.1 Lecture Grouping Strategy

The most significant innovation is the **intelligent lecture grouping mechanism**. Unlike traditional timetabling systems that schedule each section independently, this system:

- **Groups Multiple Sections**: Combines 2 sections per lecture variable
- **Dynamic Grouping**: Automatically partitions sections into optimal groups
- **Hybrid Approach**: Maintains individual labs while grouping lectures
- **Resource Optimization**: Better utilization of large lecture halls

This innovation reduces problem complexity from O(n) to O(n/2) variables for lectures while maintaining solution quality.

#### 5.1.2 Pre-computation and Caching Strategy

The system implements an advanced pre-computation strategy:
- **Instructor Qualification Cache**: Pre-computes qualified instructors per course
- **Forbidden Days Sets**: Pre-computes and stores forbidden time slots as sets for O(1) lookup
- **Room Type Filtering**: Pre-filters rooms by type and capacity
- **Dictionary-based Lookups**: Replaces expensive DataFrame operations with O(1) dictionary access

This reduces domain generation time from O(n²) to O(n) in many cases.

#### 5.1.3 Modern GUI with Advanced Filtering

The GUI implementation includes several innovative features:
- **Intelligent Section Sorting**: Sorts sections by academic level and section number
- **Dynamic Filtering**: Real-time filtering without page reload
- **Visual Encoding**: Color-coded rows and emoji indicators for quick recognition
- **Responsive Design**: Adapts to different screen sizes and data volumes

### 5.2 Problem Complexity

#### 5.2.1 Computational Complexity

The timetabling problem is **NP-Complete**, making it computationally challenging:

- **Variables**: O(n) where n is number of course-section combinations
- **Domain Size**: O(t × r × i) where t=time slots, r=rooms, i=instructors
- **Constraints**: O(n²) pairwise constraints between all variables
- **Search Space**: Exponential in worst case: O((t×r×i)^n)

#### 5.2.2 Constraint Complexity

The system handles multiple constraint types:
1. **Binary Constraints**: Between pairs of variables (O(n²) constraints)
2. **Unary Constraints**: Domain restrictions (O(n) constraints)
3. **Global Constraints**: Section overlap constraints across multiple variables

#### 5.2.3 Algorithm Complexity Analysis

**AC-3 Algorithm**:
- Time Complexity: O(cd³) where c = constraints, d = domain size
- Space Complexity: O(n) for queue and neighbor maps
- In practice: Significantly reduces search space before backtracking

**Backtracking with MRV**:
- Worst Case: O(b^d) where b = branching factor, d = depth
- Average Case: Much better with MRV heuristic and AC-3 preprocessing
- Space Complexity: O(d) for recursion stack

### 5.3 Advanced Techniques Implemented

1. **Heuristic Search**: MRV (Minimum Remaining Values) for variable selection
2. **Constraint Propagation**: AC-3 for domain pruning
3. **Forward Checking**: Consistency checking during assignment
4. **Early Termination**: Fail-fast on inconsistency detection
5. **Data Structure Optimization**: Efficient lookups and set operations

### 5.4 Extensibility

The system is designed for extensibility:
- **Additional Constraints**: Easy to add new constraint types
- **Different Grouping Strategies**: Configurable group sizes
- **Soft Constraints**: Framework supports preference-based constraints
- **Multi-objective Optimization**: Can be extended with optimization objectives

---

## Conclusion

This project successfully implements an intelligent timetabling system using CSP techniques that addresses real-world academic scheduling challenges. The system demonstrates:

1. **Effective Problem Solving**: Successfully generates feasible timetables for complex scenarios
2. **Technical Excellence**: High-quality code with performance optimizations
3. **Innovation**: Lecture grouping strategy and advanced pre-computation techniques
4. **User Experience**: Modern, interactive GUI for timetable visualization
5. **Practical Utility**: Handles real-world data and produces usable outputs

The combination of AC-3 constraint propagation, backtracking with MRV heuristic, and the innovative lecture grouping strategy creates an efficient and effective solution to the timetabling problem. The system's modular design and comprehensive error handling make it robust and maintainable.

### Future Enhancements

Potential improvements for future versions:
- **Soft Constraints**: Implement preference-based constraints with penalty functions
- **Multi-objective Optimization**: Optimize for room utilization, instructor preferences, etc.
- **Parallel Processing**: Utilize multi-threading for large-scale problems
- **Machine Learning**: Learn from historical schedules to improve future solutions

---

## References

1. Russell, S., & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson.

2. Dechter, R. (2003). *Constraint Processing*. Morgan Kaufmann.

3. Mackworth, A. K. (1977). Consistency in networks of relations. *Artificial Intelligence*, 8(1), 99-118.

4. Haralick, R. M., & Elliott, G. L. (1980). Increasing tree search efficiency for constraint satisfaction problems. *Artificial Intelligence*, 14(3), 263-313.

5. Pandas Development Team. (2023). *pandas-dev/pandas: Pandas*. Zenodo. https://doi.org/10.5281/zenodo.3509134

6. Python Software Foundation. (2023). *Python Programming Language*. https://www.python.org/

---

## Appendix A: System Requirements

- **Python Version**: 3.7 or higher
- **Required Libraries**:
  - pandas >= 1.3.0
  - tkinter (included with Python)
  - openpyxl (for Excel file reading)

## Appendix B: File Structure

```
cspProject/
├── cspGrouping.py          # Main CSP solver implementation
├── timetable_output.csv    # Generated timetable output
├── buildings_rooms.json    # Extracted building/room data (JSON)
├── buildings_rooms.csv     # Extracted building/room data (CSV)
├── Halls Timetable Fall 2025 (1).xlsx  # Input Excel file
└── web_interface/          # Web Application Source
    ├── backend/
    │   └── app.py          # Flask API Server
    └── frontend/
        ├── package.json
        ├── vite.config.js
        └── src/
            └── App.jsx     # Main React Component
```

---

**Report Prepared By**: [Your Name]  
**Date**: [Current Date]  
**Project**: Intelligent Timetabling System Using CSP


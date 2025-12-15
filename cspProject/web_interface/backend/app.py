
import sys
import os
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add parent directory to path to import cspGrouping
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

import cspGrouping

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

CSV_FOLDER_PATH = r"E:\CSP_data"

@app.route('/api/solve', methods=['GET'])
def solve_csp():
    try:
        # 1. Load Data
        dataset = cspGrouping.load_data_from_csv(CSV_FOLDER_PATH)
        if not dataset:
            return jsonify({"error": "Failed to load CSV data. Check server logs."}), 500

        # 2. Setup CSP
        csp_vars, csp_domains, csp_constraints, empty_reasons = cspGrouping.setup_csp(dataset)
        
        # 3. AC-3
        if not cspGrouping.ac3(csp_vars, csp_domains, csp_constraints):
            return jsonify({
                "status": "failure",
                "message": "No solution possible (Inconsistent constraints)."
            }), 200

        # 4. Backtracking Solver
        # Note: In a real web app, we might want to run this in a background thread/job queue
        # if it takes too long, but for now we'll run it synchronously.
        solver_domains = {var: list(dom) for var, dom in csp_domains.items()}
        final_schedule = cspGrouping.solve_backtracking(csp_vars, solver_domains, {})

        if not final_schedule:
            return jsonify({
                "status": "failure", 
                "message": "No solution found after backtracking."
            }), 200

        # 5. Format Output for Frontend
        formatted_schedule = []
        
        # Create lookups (borrowed logic from display_and_save_timetable)
        timeslots_dict = dataset['timeslots'].set_index('TimeSlotID').to_dict('index')
        instructors_dict = dataset['instructors'].set_index('InstructorID').to_dict('index')

        for variable, (time_id, room_id, instructor_id) in final_schedule.items():
            parts = variable.split('_')
            course_id = parts[0]
            var_type = parts[1] # Lecture or Lab
            
            sections = cspGrouping.get_sections_from_var(variable)
            if not sections: continue

            time_details = timeslots_dict.get(time_id)
            instructor_info = instructors_dict.get(instructor_id)
            
            if not time_details or not instructor_info: continue

            formatted_schedule.append({
                "id": variable + "_" + time_id, # Unique key for React
                "course": course_id,
                "type": var_type,
                "sections": sorted(list(sections)),
                "instructor": instructor_info.get('Name', 'N/A'),
                "room": room_id,
                "day": time_details.get('Day', 'N/A'),
                "startTime": time_details.get('StartTime', 'N/A'),
                "endTime": time_details.get('EndTime', 'N/A'),
                "colorType": "lecture" if var_type == "Lecture" else "lab"
            })

        return jsonify({
            "status": "success",
            "data": formatted_schedule
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

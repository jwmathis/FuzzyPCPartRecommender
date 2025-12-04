from flask import Flask, jsonify, request, render_template_string
# Update imports from the renamed file
from fuzzifying_parts import (
    get_best_part_recommendation,
    fuzzify_gpu_data,
    fuzzify_cpu_data,
    fuzzify_mb_data
)
from gpu_data import gpu_dataset
from cpu_data import cpu_dataset
from motherboard_data import motherboard_dataset

app = Flask(__name__)


# --- API Endpoint to run Fuzzy Logic ---
@app.route('/recommend', methods=['POST'])
def recommend_parts():
    """
    Processes the entire GPU dataset through the fuzzy logic system
    and selects the single best GPU.
    """
    try:
        # 1. Get user inputs from the JSON body
        user_inputs = request.get_json()

        # Extract user preferences (matching the IDs from index.html)
        # Note: 'aesthetics' from HTML maps to 'resolution_level' here.
        user_inputs_clean = {
            'budget': user_inputs.get('budget', 1500),
            'performance_priority': user_inputs.get('performance', 7),  # 'performance' is the ID in HTML
            'resolution_level': user_inputs.get('aesthetics', 2)  # 'aesthetics' is the ID in HTML
        }

        # Simple input validation (e.g., ensure budget is a reasonable number)
        if not (500 <= user_inputs_clean['budget'] <= 3000):
            return jsonify({"error": "Budget out of range (500-3000)."}), 400

    except Exception as e:
        return jsonify({"error": f"Invalid JSON or request format: {e}"}), 400

    # Define the number of recommendations you want
    NUM_RECOMMENDATIONS = 3

    GPU_BUDGET_RATIO = 0.45
    CPU_BUDGET_RATIO = 0.30
    MB_BUDGET_RATIO = 0.25
    # User's total budget
    total_budget = user_inputs_clean['budget']

    # Calculate allocated budget for each part
    allocated_gpu_budget = total_budget * GPU_BUDGET_RATIO
    allocated_cpu_budget = total_budget * CPU_BUDGET_RATIO
    allocated_mb_budget = total_budget * MB_BUDGET_RATIO

    # Update user_inputs_clean for recommendation functions
    user_inputs_clean['allocated_gpu_budget'] = allocated_gpu_budget
    user_inputs_clean['allocated_cpu_budget'] = allocated_cpu_budget
    user_inputs_clean['allocated_mb_budget'] = allocated_mb_budget

    # 1. Get ranked GPUs
    ranked_gpus = get_best_part_recommendation(
        user_inputs_clean,
        gpu_dataset,
        lambda part: (fuzzify_gpu_data(part)[1], fuzzify_gpu_data(part)[2]),
        'gpu'
    )

    # 2. Get ranked CPUs
    ranked_cpus = get_best_part_recommendation(
        user_inputs_clean,
        cpu_dataset,
        fuzzify_cpu_data,
        'CPU'
    )

    # 3. Get ranked MBs
    ranked_mb = get_best_part_recommendation(
        user_inputs_clean,
        motherboard_dataset,
        lambda part: (fuzzify_mb_data(part)[1], fuzzify_mb_data(part)[2]),
        'MB'
    )

    if not ranked_gpus or not ranked_cpus:
        return jsonify({"error": "Failed to generate recommendations for one or more parts."}), 500

    # 3. Select the top N parts
    top_cpus = ranked_cpus[:NUM_RECOMMENDATIONS]
    top_gpus = ranked_gpus[:NUM_RECOMMENDATIONS]
    top_mbs = ranked_mb[:NUM_RECOMMENDATIONS]

    # 4. Create the final response structure with arrays
    final_recommendation = {
        "CPU_Recommendations": top_cpus,
        "GPU_Recommendations": top_gpus,
        "MB_Recommendations": top_mbs,
    }

    # 5. Return the structured JSON
    return jsonify(final_recommendation)


# --- Basic Route to serve the HTML/JS frontend ---
@app.route('/')
def index():
    """Renders the HTML file directly for the frontend."""
    return render_template_string(open('index.html').read())


if __name__ == '__main__':
    app.run(debug=True)
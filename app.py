from flask import Flask, jsonify, render_template_string, request
from fuzzifying_gpu_data import get_gpu_recommendations
from gpu_data import gpu_dataset

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

    # 2. Get ranked GPUs
    # This function handles the fuzzification and scoring logic
    ranked_gpus = get_gpu_recommendations(user_inputs_clean, gpu_dataset)

    if not ranked_gpus:
        return jsonify({"error": "No GPU recommendations could be generated."}), 500

    # 3. Select the single best part for the frontend display
    best_gpu = ranked_gpus[0]

    # 4. Create the final response structure to match the frontend (CPU, GPU, MB)
    # Since you only have GPU logic now, we mock the other two parts.
    final_recommendation = {
        "CPU": {
            "name": "MOCK CPU (Placeholder)",
            "score": "N/A"  # In a real system, this would be the best CPU
        },
        "GPU": {
            "name": best_gpu['model'],
            "score": f"{best_gpu['reco_score']:.2f}%",
            "price": best_gpu['price_usd'],
            "details": best_gpu
        },
        "Motherboard": {
            "name": "MOCK Motherboard (Placeholder)",
            "score": "N/A"
        }
    }

    # 5. Return the single best GPU along with placeholders
    return jsonify(final_recommendation)


# --- Basic Route to serve the HTML/JS frontend ---
@app.route('/')
def index():
    """Renders the HTML file directly for the frontend."""
    return render_template_string(open('index.html').read())


if __name__ == '__main__':
    # Flask is usually run using 'flask run', but this structure works for simple execution.
    app.run(debug=True)
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from fuzzy_logic_recommender import get_reco_score, normalize_budget


# Helper function to map user preference scales (1-10 or 1-3) to a 0-100 fuzzy input scale
def map_user_input_to_100(value, max_scale):
    """Maps a user input (e.g., 1-10) to the fuzzy system's 0-100 universe"""
    # Clamp value to be at least 1
    value = max(1, value)
    return 100 * (value - 1) / (max_scale - 1)


# Define max scores for normalization based on your dataset
MAX_SINGLE_CORE = 5000
MAX_MULTI_CORE = 64000
MAX_CUDA_CORES = 16500
MAX_VRAM_GB = 24
MAX_FEATURES_SCORE = 100


def fuzzify_gpu_data(gpu_data):
    """
    Translates raw GPU specs into normalized 0-100 scores for Performance and Resolution.
    These scores represent the part's CAPABILITY.

    NOTE: The GPU's price is NOT used here, but in the final ranking function.
    """

    # 1. Fuzzify Performance Priority (Part's Capability)
    # Combine CUDA cores (70%) and VRAM (30%) for a raw performance score.
    perf_score_part = (
                              (gpu_data['cuda_cores'] / MAX_CUDA_CORES) * 0.7 +
                              (gpu_data['vram_gb'] / MAX_VRAM_GB) * 0.3
                      ) * 100

    perf_score_part = max(0, min(100, perf_score_part))

    # 2. Fuzzify the Preferred Resolution Score (Part's Capability)
    if gpu_data['vram_gb'] >= 16 and gpu_data['cuda_cores'] > 10000:
        resolution_score_part = 90  # High resolution (4K)
    elif gpu_data['vram_gb'] >= 8 and gpu_data['cuda_cores'] > 5000:
        resolution_score_part = 50  # Medium resolution (1440p)
    else:
        resolution_score_part = 10  # Low resolution (1080p)

    # Return the part's CAPABILITY scores
    return perf_score_part, resolution_score_part


def fuzzify_cpu_data(cpu_data):
    """
    Translates raw CPU specs into normalized 0-100 scores for Price and Performance.
    """

    # 1. Fuzzify Performance Priority (Part's Capability)
    perf_score_part = (
                              (cpu_data['single_core_score'] / MAX_SINGLE_CORE) * 0.6 +
                              (cpu_data['multi_core_score'] / MAX_MULTI_CORE) * 0.4
                      ) * 100

    perf_score_part = max(0, min(100, perf_score_part))

    # 2. Fuzzify Resolution Score (Part's Capability)
    if perf_score_part > 80:
        resolution_score_part = 90
    elif perf_score_part > 50:
        resolution_score_part = 50
    else:
        resolution_score_part = 10

    # Return the part's CAPABILITY scores
    return perf_score_part, resolution_score_part


def fuzzify_motherboard_data(mb_data):
    """
    Translates raw Motherboard features into a normalized 0-100 score.
    :param mb_data:
    :return:
    """
    # Use the built-in features score as the 'performance' metric
    perf_score_part = (mb_data.get('features_score', 0) / MAX_FEATURES_SCORE) * 100

    # Resolution score is set low as MB does not directly affect resolution
    resolution_score_part = 10

    return perf_score_part, resolution_score_part


def get_best_part_recommendation(user_inputs, part_dataset, fuzzification_func, part_type='CPU',
                                 part_price_key='price_usd'):
    """
    Calculates the final recommendation score for any part type based on user inputs.
    Applies the crisp budget penalty based on allocated budget.
    """

    # 1. Determine the correct ALLOCATED budget based on the part type
    if part_type == 'GPU':
        allocated_budget = user_inputs['allocated_gpu_budget']
        # The user's input for performance and resolution priorities
        user_perf_n = map_user_input_to_100(user_inputs['performance_priority'], 10)
        user_res_n = map_user_input_to_100(user_inputs['resolution_level'], 3)
    elif part_type == 'CPU':
        allocated_budget = user_inputs['allocated_cpu_budget']
        user_perf_n = map_user_input_to_100(user_inputs['performance_priority'], 10)
        user_res_n = map_user_input_to_100(user_inputs['resolution_level'], 3)
    elif part_type == 'Motherboard':
        allocated_budget = user_inputs['budget'] * 0.15  # 15% allocation for MB (Example)
        # Motherboards are driven less by performance and more by features/value
        user_perf_n = map_user_input_to_100(user_inputs['performance_priority'],
                                            10)  # Use perf priority for feature desire
        user_res_n = 50  # Set resolution input to medium for Motherboard rules

        # Crisp compatibility checks (needed for full app)
        required_socket = user_inputs.get('required_socket')
        required_ram = user_inputs.get('required_ram_type')

    else:
        # Fallback
        allocated_budget = user_inputs['budget'] / 3
        user_perf_n = 50
        user_res_n = 50

    # Map user's overall total budget preference to a 0-100 scale (User's input to Fuzzy System)
    user_budget_n = normalize_budget(user_inputs['budget'])

    ranked_parts = []

    for part in part_dataset:

        # Handle Motherboard compatibility filtering
        if part_type == 'Motherboard':
            # Skip incompatible parts in a live system, but not relevant for this GPU-only test
            pass
            # For a full system:
            # if part.get('socket') != required_socket or part.get('ram_type') != required_ram:
            #     continue

        # Get the part's CAPABILITY scores (p_part, r_part) from the specific fuzzification function
        p_part, r_part = fuzzification_func(part)

        # --- 1. Calculate Raw Fuzzy Score (Using User's Budget Level) ---
        # The fuzzy logic runs with: USER's budget preference, PART's performance, PART's resolution
        reco_score_raw = get_reco_score(user_budget_n, p_part, r_part)
        final_reco_score = reco_score_raw

        # --- 2. Apply Hard Budget Penalty (Crisp Filter) ---
        part_price = part.get(part_price_key, 0)

        if part_price > allocated_budget:
            # 1. Calculate how much the price exceeds the ALLOCATED budget as a ratio
            exceed_ratio = (part_price - allocated_budget) / allocated_budget

            # 2. Apply a penalty factor (higher ratio = higher penalty)
            penalty_factor = max(0.1, 1 - (exceed_ratio * 0.75))

            final_reco_score = reco_score_raw * penalty_factor

        # --- 3. Apply Small Efficiency Bonus ---
        elif part_price <= allocated_budget * 0.95 and part_price >= allocated_budget * 0.6:
            # Reward parts that are good value and come in 5%-40% under budget
            final_reco_score = min(100.0, reco_score_raw * 1.05)

        ranked_parts.append({
            'model': part['model'],
            'reco_score': final_reco_score,
            'price_usd': part_price,
            'fuzzified_scores': {
                'performance': round(p_part, 2),
                'resolution': round(r_part, 2)
            }
        })

    # Sort and return the ranked list
    ranked_parts.sort(key=lambda x: x['reco_score'], reverse=True)
    return ranked_parts


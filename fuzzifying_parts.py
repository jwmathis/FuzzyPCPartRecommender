import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from fuzzy_logic_recommender import get_reco_score, normalize_budget

# Motherboard Chipset Hierarchy for Capability Scoring (0-100)
CHIPSET_PERFORMANCE_SCORES = {
    # High-End (Overclocking, Max I/O, DDR5)
    'X670E': 100, 'Z790': 95,
    # Mid-Range (Good I/O, some OC, likely DDR5)
    'B650': 75, 'B760': 70, 'X570': 60,
    # Budget/Entry (Basic, limited I/O/OC, often DDR4)
    'B550': 45, 'H610': 30
}

# Helper function to map user preference scales (1-10 or 1-3) to a 0-100 fuzzy input scale
def map_user_input_to_100(value, max_scale):
    """Maps a user input (e.g., 1-10) to the fuzzy system's 0-100 universe"""
    value = max(1, value)
    return 100 * (value - 1) / (max_scale - 1)

# 2. Fuzzify the raw data
# Translate data into a 0-100 score for the fuzzy system's inputs

def fuzzify_gpu_data(gpu_data):
    """
    Translates raw GPU specs into normalized 0-100 scores based on what the part OFFERS.
    These scores represent the part's CAPABILITY.
    :param gpu_data:
    :return:
    """

    # 2.1: Fuzzify the budget
    # Will be an inverse relationship: a lower price means a higher "budget score"
    # since it will leave room for buying other components.
    min_price = 500
    max_price = 3000

    price_range = max_price - min_price
    if price_range <= 0:
        budget_score = 50.0
    else:
        # Calculate normalized price (0 if min_price, 100 if max_price)
        normalized_price = 100 * (gpu_data['price_usd'] - min_price) / price_range
        # Invert the score: 100 for low price, 0 for high price
        budget_score = 100 - normalized_price

    budget_score = max(0, min(100, budget_score))  # Clamp

    # 2.2: Fuzzify Performance Priority
    # Will combine VRAM and CUDA Cores for a score
    # The higher the numbers, the higher the performance.
    # -----FUTURE: Potentially Implement Fuzzy Logic here too ----
    # Define fuzzy sets for VRAM and CUDA Cores
    vram_universe = np.arange(0, 25, 1) # VRAM in GB
    cuda_universe = np.arange(0, 15001, 1)  # CUDA cores

    vram_low = fuzz.trimf(vram_universe, [0, 0, 8])
    vram_medium = fuzz.trimf(vram_universe, [4, 8, 16])
    vram_high = fuzz.trimf(vram_universe, [8, 16, 24])

    cuda_low = fuzz.trimf(cuda_universe, [0, 0, 4000])
    cuda_medium = fuzz.trimf(cuda_universe, [2000, 6000, 10000])
    cuda_high = fuzz.trimf(cuda_universe, [8000, 12000, 15000])

    # Fuzzify GPU's actual values
    vram_score = fuzz.interp_membership(vram_universe, vram_high, gpu_data['vram_gb'])
    cuda_score = fuzz.interp_membership(cuda_universe, cuda_high, gpu_data['cuda_cores'])

    # Combine the two scores for a final performance score.
    # Using a simple weighted average or potentially update to use a fuzzy rule
    # Using simple approach: CUDA cores will be worth 70% of the score and VRAM will be worth 30% of the score
    max_cuda = 16500
    max_vram = 24

    perf_score = (
        (gpu_data['cuda_cores'] / max_cuda) * 0.7 +
        (gpu_data['vram_gb'] / max_vram) * 0.3
    ) * 100

    # Clamp the score to be within 0-100
    perf_score = max(0, min(100, perf_score))

    # 2.3: Fuzzify the Preferred Resolution Score
    # This is a direct mapping based on VRAM and core count.
    # 1080p builds are typically happy with 6-8GB VRAM.
    # 1440p is the "sweet spot" at 8-12GB.
    # 4K requires 16GB+.
    if gpu_data['vram_gb'] >= 16 and gpu_data['cuda_cores'] > 10000:
        resolution_score = 90  # High resolution (4K)
    elif gpu_data['vram_gb'] >= 8 and gpu_data['cuda_cores'] > 5000:
        resolution_score = 50  # Medium resolution (1440p)
    else:
        resolution_score = 10  # Low resolution (1080p)

    return budget_score, perf_score, resolution_score

# Define max scores for normalization based on your dataset
MAX_SINGLE_CORE = 5000
MAX_MULTI_CORE = 64000  # From 14900K

def fuzzify_cpu_data(cpu_data):
    """
    Translates raw CPU specs into normalized 0-100 scores for Price and Performance.
    """

    # --- 2.1: Fuzzify Performance Priority (Part's Capability) ---
    # CPU performance score should be a weighted average of single-core and multi-core.
    # Weight single-core higher (e.g., 60%) for general-purpose PC builds.
    perf_score_part = (
                              (cpu_data['single_core_score'] / MAX_SINGLE_CORE) * 0.6 +
                              (cpu_data['multi_core_score'] / MAX_MULTI_CORE) * 0.4
                      ) * 100

    perf_score_part = max(0, min(100, perf_score_part))

    # --- 2.2: Fuzzify Resolution Score (Part's Capability) ---
    # The CPU generally has less impact on resolution than the GPU,
    # but a high-end CPU is needed to prevent a GPU bottleneck at 4K.
    # Assign a score based on raw power to match user's resolution preference.
    if perf_score_part > 80:
        resolution_score_part = 90  # High (4K capable)
    elif perf_score_part > 50:
        resolution_score_part = 50  # Medium (1440p capable)
    else:
        resolution_score_part = 10  # Low (1080p capable)

    # Return the part's CAPABILITY scores
    return perf_score_part, resolution_score_part  # Only two scores needed

def fuzzify_mb_data(mb_data):
    """
    Translates raw Motherboard specs into normalized 0-100 scores for Price and Performance.
    :param mb_data:
    :return: (budget score, perf_score, resolution_score - mapped to Feature Score)
    """

    # 2.1 Fuzzify budget
    min_price = 500
    max_price = 3000

    price_range = max_price - min_price
    if price_range <= 0:
        budget_score = 50.0
    else:
        # Calculate normalized price (0 if min_price, 100 if max_price)
        normalized_price = 100 * (mb_data['price_usd'] - min_price) / price_range
        # Invert the score: 100 for low price, 0 for high price
        budget_score = 100 - normalized_price

    budget_score = max(0, min(100, budget_score))  # Clamp

    # 2.2 Fuzzify Performance score (based on Chipset Tier)
    chipset = mb_data['chipset']
    perf_score = CHIPSET_PERFORMANCE_SCORES.get(chipset, 30) # Default to low score

    # Apply a boost for DDR5 generation (future-proofing/highest speeds)
    if mb_data['ram_gen'] == 'DDR5':
        perf_score = min(100, perf_score + 10)
    # 2.3 Fuzzify future-proofing socre (mapped to resolution score)
    future_proofing_score = 0
    if mb_data['ram_gen'] == 'DDR5':
        future_proofing_score += 50 # Base for DDR5
    if 'E' in chipset or 'Z' in chipset: # High-end chipsets (X670E, Z790)
        future_proofing_score += 40

    resolution_score = max(10, min(100, future_proofing_score))

    return budget_score, perf_score, resolution_score

def get_best_part_recommendation(user_inputs, part_dataset, fuzzification_func, part_type='CPU', part_price_key='price_usd'):
    """
    Calculates the final recommendation score for any part type based on user inputs.
    """
    # 1. Determine the correct ALLOCATED budget based on the part type
    if part_type == 'GPU':
        # total_budget * 0.45
        allocated_budget = user_inputs['allocated_gpu_budget']
    elif part_type == 'CPU':
        # total_budget * 0.30
        allocated_budget = user_inputs['allocated_cpu_budget']
    elif part_type == 'MB':
        # total_budget * 0.25
        allocated_budget = user_inputs['allocated_mb_budget']
    else:
        # Fallback or error handling for unassigned parts
        allocated_budget = user_inputs['budget'] / 3


    ranked_parts = []

    # 1. Map user inputs to the fuzzy system's 0-100 scale
    user_budget_n = normalize_budget(user_inputs['budget'])
    user_perf_n = map_user_input_to_100(user_inputs['performance_priority'], 10)
    user_res_n = map_user_input_to_100(user_inputs['resolution_level'], 3)

    for part in part_dataset:

        # Get the part's CAPABILITY scores (p_part, r_part) from the specific fuzzification function
        # NOTE: CPU fuzzification only returns 2 scores, GPU returns 3.
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

            # 2. Apply a penalty factor. The more it exceeds, the lower the factor.
            # Example: 100% over budget (exceed_ratio=1.0) leads to 1 - (1.0 * 0.75) = 0.25 factor
            # 0% over budget (exceed_ratio=0) leads to 1.0 factor (no penalty)
            # Ensure the penalty factor does not drop below 0.1 to avoid giving a score of 0.
            penalty_factor = max(0.1, 1 - (exceed_ratio * 0.75))

            final_reco_score = reco_score_raw * penalty_factor

            # Apply Small Efficiency Bonus
            # Reward parts that are good value and come in under the allocated budget threshold
        elif part_price <= allocated_budget * 0.95:
            # Apply a minor bonus if the part price is 5% or more under the allocated budget
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


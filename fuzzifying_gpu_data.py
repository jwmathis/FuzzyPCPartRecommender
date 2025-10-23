import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from fuzzy_logic_recommender import get_reco_score, normalize_budget

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
    # Define a simple conversion based on a hypothetical rang eof values.
    # Use a 0-100 scale for this metric/

    # 2.1: Fuzzify the budget
    # Will be an inverse relationship: a lower price means a higher "budget score"
    # since it will leave room for buying other components.
    # Will assume a "very low budget" is $500 and a "very high budget" is $3000
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
    # -----Potentially Implement Fuzzy Logic here too ----
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


def get_gpu_recommendations(user_inputs, gpu_dataset):
    """
    Calculates the final recommendation score for all GPUs based on user inputs.
    """
    ranked_gpus = []

    # 1. Map user inputs to the fuzzy system's 0-100 scale
    user_budget_n = normalize_budget(user_inputs['budget'])
    user_perf_n = map_user_input_to_100(user_inputs['performance_priority'], 10)
    user_res_n = map_user_input_to_100(user_inputs['resolution_level'], 3)

    # The user inputs are now the crisp inputs for the fuzzy system!

    # 2. Run the user's preference through the fuzzy system to get a TARGET score.
    # The fuzzy system will essentially tell us: "Based on what the user wants,
    # what kind of part (low/med/high) should the system recommend?"
    # This is not strictly necessary for this simple rule set, but it keeps the
    # structure aligned with a more complex fuzzy system.
    # For a simpler approach (which is all you need for now): we compare part scores to user scores.

    for gpu in gpu_dataset:

        # Get the part's CAPABILITY scores (0-100)
        b_part, p_part, r_part = fuzzify_gpu_data(gpu)

        # --- Calculate Match Score ---
        # The Match Score determines how well the part's CAPABILITY aligns with the USER'S WANTS.
        # This is the crucial step. We use the *part's capability scores* as the inputs
        # to the fuzzy system, but using the *user's normalized scores* as the 'target'.

        # A simpler approach: Compare the Part's score to the User's score.
        # This determines *how good* a match the part is for the user's *preference level*.
        # We use the *part's scores* as inputs to the fuzzy engine.

        # The fuzzy logic *already* gives us a final score based on the inputs.
        # We'll use the PART's capability scores (b_part, p_part, r_part)
        # as the crisp inputs for the fuzzy logic engine.

        # This is the **most straightforward** way to combine your existing files:
        # We assume a GPU with high B/P/R scores will be a "high" recommendation
        # and then filter the results to find the *best* part within the user's budget.

        reco_score_raw = get_reco_score(b_part, p_part, r_part)

        if reco_score_raw is not None:

            # --- Final Score Adjustment (Crucial for Budget) ---
            # If the GPU price exceeds the user's budget, penalize the score heavily.
            # This is a crisp filter applied after the fuzzy logic.
            final_reco_score = reco_score_raw
            if gpu['price_usd'] > user_inputs['budget']:
                # Heavy penalty if price exceeds budget
                penalty_factor = (gpu['price_usd'] - user_inputs['budget']) / user_inputs['budget']
                final_reco_score = reco_score_raw * max(0.1, (1 - penalty_factor))  # Max penalty to 90%

            # If the GPU is a gross overkill for a low budget, penalize slightly.
            if gpu['price_usd'] < user_inputs['budget'] * 0.5 and user_inputs['budget'] < 1000:
                final_reco_score *= 0.95  # Slight penalty for going too cheap/overkill part

            ranked_gpus.append({
                'model': gpu['model'],
                'reco_score': final_reco_score,
                'price_usd': gpu['price_usd'],
                'fuzzified_scores': {
                    'budget': round(b_part, 2),
                    'performance': round(p_part, 2),
                    'resolution': round(r_part, 2)
                }
            })

    # Sort the list by 'reco_score' in descending order
    ranked_gpus.sort(key=lambda x: x['reco_score'], reverse=True)

    return ranked_gpus
# # Step 3: Run the fuzzified data through the fuzzy recommender.
# if __name__ == '__main__':
#
#     # A list to store the final results for ranking
#     ranked_gpus = []
#
#     print("--- Starting Fuzzy Logic Analysis of GPU Dataset ---")
#
#     # This loop processes each GPU dictionary one by one, fixing the TypeError.
#     for gpu in gpu_dataset:
#
#         # 'gpu' is the current dictionary, allowing us to access 'model'
#         print(f"\n--- Analyzing GPU: {gpu['model']} ---")
#
#         # Get the fuzzified scores (passing only the current GPU dictionary)
#         b_score, p_score, r_score = fuzzify_gpu_data(gpu)
#
#         print(f"Fuzzified Scores for {gpu['model']}:")
#         print(f"  Budget Score: {b_score:.2f}")
#         print(f"  Performance Score: {p_score:.2f}")
#         print(f"  Resolution Score: {r_score:.2f}")
#
#         # Use these scores as inputs for our fuzzy recommender
#         # NOTE: This uses the imported get_reco_score (which you'll define in fuzzy_logic_recommender.py)
#         reco = get_reco_score(b_score, p_score, r_score)
#
#         if reco is not None:
#             print(f"Final Fuzzy Recommendation Score for this GPU: {reco:.2f}")
#             # Store the result for later ranking
#             ranked_gpus.append({
#                 'model': gpu['model'],
#                 'reco_score': reco,
#                 'price_usd': gpu['price_usd']
#             })
#         else:
#             print("Could not compute a recommendation score.")
#
#     print("\n\n--- Final Ranking ---")
#
#     # Sort the list by 'reco_score' in descending order
#     ranked_gpus.sort(key=lambda x: x['reco_score'], reverse=True)
#
#     # Print the top 5 recommendations
#     for i, item in enumerate(ranked_gpus[:5]):
#         print(f"#{i + 1}: {item['model']} (Score: {item['reco_score']:.2f}, Price: ${item['price_usd']:.2f})")
#
#     print("-----------------------------------")

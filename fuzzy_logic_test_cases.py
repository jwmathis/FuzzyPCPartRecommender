from fuzzifying_parts import get_best_part_recommendation, fuzzify_gpu_data
from gpu_data import gpu_dataset
from fuzzy_logic_recommender import normalize_budget  # Used for context

# --- GLOBAL CONFIGURATION ---
GPU_BUDGET_RATIO = 0.45  # Allocate 45% of the total budget to the GPU


def run_test_case(test_name, total_budget, perf_priority, resolution_level):
    """Runs the recommender for a specific user scenario and prints results."""

    # 1. Calculate Allocated Budget (CRITICAL STEP)
    allocated_gpu_budget = total_budget * GPU_BUDGET_RATIO

    # 2. Define Clean User Inputs
    user_inputs_clean = {
        'budget': total_budget,
        'performance_priority': perf_priority,  # 1-10 scale
        'resolution_level': resolution_level,  # 1-3 scale
        'allocated_gpu_budget': allocated_gpu_budget,
        'allocated_cpu_budget': total_budget * 0.25  # Mock CPU allocation for context
    }

    # 3. Run Recommender
    ranked_gpus = get_best_part_recommendation(
        user_inputs_clean,
        gpu_dataset,
        fuzzify_gpu_data,
        part_type='GPU'
    )

    # 4. Print Results
    budget_n = normalize_budget(total_budget)
    print(f"\n=======================================================")
    print(f"TEST CASE: {test_name}")
    print(f"-------------------------------------------------------")
    print(f"Total Budget: ${total_budget:,.2f} (Fuzzy Input: {budget_n:.2f})")
    print(f"GPU Allocated Budget (45%): ${allocated_gpu_budget:,.2f}")
    print(f"Performance Priority (1-10): {perf_priority}, Resolution (1-3): {resolution_level}")
    print(f"=======================================================")

    print(
        f"| {'#':<2} | {'Model':<20} | {'Price':<8} | {'Raw Score (Fuzzy)':<20} | {'Final Score':<15} | {'Budget vs Alloc.':<18} |")
    print(f"| --- | -------------------- | -------- | -------------------- | --------------- | ------------------ |")

    for i, item in enumerate(ranked_gpus):
        price = item['price_usd']

        # Calculate penalty context for display
        budget_context = ""
        if price > allocated_gpu_budget:
            exceed_amount = price - allocated_gpu_budget
            budget_context = f"OVER ({-exceed_amount:,.0f})"
        elif price <= allocated_gpu_budget * 0.95:
            budget_context = "UNDER (Bonus)"
        else:
            budget_context = "Perfect Match"

        # The 'Raw Score' is not explicitly returned, but we use the fuzzified scores + final score for demonstration
        # NOTE: The raw score is internally calculated by get_reco_score

        print(
            f"| {i + 1:<2} | {item['model']:<20} | ${price:,.0f} | {'N/A (Fuzzy Logic)':<20} | {item['reco_score']:.2f} | {budget_context:<18} |")


# --------------------------------------------------------------------------
# --- Test Execution ---
# --------------------------------------------------------------------------

# SCENARIO 1: High Budget, High Performance (Targeting 4K)
# Budget is $3000. Allocated GPU budget is $1350.
# The system should prioritize the RTX 4070 Ti SUPER because the 4090 is too far over budget.
run_test_case(
    test_name="HIGH-END BUILD (BUDGET: $3000, PRIO: 10/3)",
    total_budget=3000,
    perf_priority=10,
    resolution_level=3
)

# SCENARIO 2: Medium Budget, Medium Performance (Targeting 1440p)
# Budget is $1500. Allocated GPU budget is $675.
# The system should strongly favor the RTX 4070 Ti SUPER or RX 7700 XT as they are closest to/under $675.
run_test_case(
    test_name="MID-RANGE BUILD (BUDGET: $1500, PRIO: 6/2)",
    total_budget=1500,
    perf_priority=6,
    resolution_level=2
)

# SCENARIO 3: Budget Build, Low Priority (Targeting 1080p)
# Budget is $1000. Allocated GPU budget is $450.
# The system should strongly favor the RX 7700 XT and the RTX 3050 for value.
run_test_case(
    test_name="BUDGET BUILD (BUDGET: $1000, PRIO: 3/1)",
    total_budget=1000,
    perf_priority=3,
    resolution_level=1
)

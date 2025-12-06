import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt

# --- CONFIGURATION: Defining budget boundaries for the project ---
MIN_BUDGET = 500 # Minimum dollar amount for a functional PC
MAX_BUDGET = 3000 # Maximum high-end dollar amount the system considers 'high'


# -------------------------------------------------
# Budget normalization
# -------------------------------------------------
def normalize_budget(dollar_value):
    """
    Converts real-world dollar amount into the fuzzy system's 0-100 scale.
    :param dollar_value:
    :return:
    """

    # Calculate the range of the real-world budget
    budget_range = MAX_BUDGET - MIN_BUDGET

    if dollar_value <= MIN_BUDGET:
        return 0.0
    if dollar_value >= MAX_BUDGET:
        return 100.0

    # Calculate the position within the 0-100 scale
    normalized_score = 100 * (dollar_value - MIN_BUDGET) / budget_range

    # Ensure the score is exactly within the 0 to 100 bounds
    return max(0.0, min(100.0, normalized_score))

# -------------------------------------------------
# 1. Fuzzification (Defining Fuzzy Variables and Membership functions)
#       Take crisp inputs and convert them into fuzzy sets.
# -------------------------------------------------

UOD = np.arange(0, 101, 1)

# --- Antecedent (Input) Variables ---

# User's Budget Capability Score (0=Very Low, 100=Very High)
budget = ctrl.Antecedent(UOD, 'budget')
# Part's Performance Capability Score (0=Very Low, 100=Very High)
performance_priority = ctrl.Antecedent(UOD, 'performance_priority')
# Part's Resolution Capability Score (0=Very Low, 100=Very High)
preferred_resolution = ctrl.Antecedent(UOD, 'preferred_resolution')

# --- Consequent (Output) Variable ---
recommendation_score = ctrl.Consequent(UOD, 'recommendation_score')


# -------------------------------------------------
# 2. Define Membership Functions (Fuzzy Sets)
#       Create Membership Functions for each variable
#       Using triangular membership functions for simplicity
#       Parameters are [start, peak, end] of the triangle
# -------------------------------------------------

# Input Membership Functions
budget['low'] = fuzz.trapmf(UOD, [0, 0, 25, 50])
budget['medium'] = fuzz.trimf(UOD, [25, 50, 75])
budget['high'] = fuzz.trapmf(UOD, [50, 75, 100, 100])

performance_priority['low'] = fuzz.trapmf(UOD, [0, 0, 20, 50])
performance_priority['medium'] = fuzz.trimf(UOD, [20, 50, 80])
performance_priority['high'] = fuzz.trapmf(UOD, [50, 80, 100, 100])

preferred_resolution['low'] = fuzz.trapmf(UOD, [0, 0, 30, 60])
preferred_resolution['medium'] = fuzz.trimf(UOD, [30, 60, 90])
preferred_resolution['high'] = fuzz.trapmf(UOD, [60, 90, 100, 100])

# Output Membership Functions (Recommendation Score)
recommendation_score['poor'] = fuzz.trapmf(UOD, [0, 0, 10, 30])
recommendation_score['average'] = fuzz.trimf(UOD, [10, 40, 70])
recommendation_score['high'] = fuzz.trimf(UOD, [40, 75, 95])
recommendation_score['excellent'] = fuzz.trapmf(UOD, [70, 95, 100, 100])



# -------------------------------------------------
# 3. Define the Fuzzy Rules (The Knowledge Base)
#   Defining a set of IF-THEN rules that link
#       the inputs to the desired output.
#   Example: IF budget is high AND performance is high, THEN the recommendation score is high
# -------------------------------------------------
# Short aliases for clarity in rule definition
BS_L, BS_M, BS_H = budget['low'], budget['medium'], budget['high']
PC_L, PC_M, PC_H = performance_priority['low'], performance_priority['medium'], performance_priority['high']
RC_L, RC_M, RC_H = preferred_resolution['low'], preferred_resolution['medium'], preferred_resolution['high']

R_P, R_A, R_H, R_E = recommendation_score['poor'], recommendation_score['average'], recommendation_score['high'], recommendation_score['excellent']

rules = [
    # --- 1. LOW Budget (BS_L) Rules (9 Rules) ---
    # Low Performance Priority
    ctrl.Rule(BS_L & PC_L & RC_L, R_P),       # Matched low-end target
    ctrl.Rule(BS_L & PC_L & RC_M, R_P),       # Budget limits medium res goal
    ctrl.Rule(BS_L & PC_L & RC_H, R_P),       # Major mismatch: too low budget for high res

    # Medium Performance Priority
    ctrl.Rule(BS_L & PC_M & RC_L, R_A),       # Slight overspend on part, but still limited by budget
    ctrl.Rule(BS_L & PC_M & RC_M, R_A),       # Decent part, but budget is a constraint
    ctrl.Rule(BS_L & PC_M & RC_H, R_P),       # Big mismatch: cannot achieve high res with low budget

    # High Performance Priority
    ctrl.Rule(BS_L & PC_H & RC_L, R_H),       # Excellent value: Great part for a low-res target, despite budget
    ctrl.Rule(BS_L & PC_H & RC_M, R_H),       # High value match: Best part for budget, good for mid-res
    ctrl.Rule(BS_L & PC_H & RC_H, R_H),       # High value match: Max possible perf for high res, limited by budget

    # --- 2. MEDIUM Budget (BS_M) Rules (9 Rules) ---
    # Low Performance Priority
    ctrl.Rule(BS_M & PC_L & RC_L, R_A),       # Overspending on a low-end part
    ctrl.Rule(BS_M & PC_L & RC_M, R_A),       # Mismatch: Too much budget for low performance part
    ctrl.Rule(BS_M & PC_L & RC_H, R_A),       # Mismatch: Low perf cannot hit high res, despite budget

    # Medium Performance Priority
    ctrl.Rule(BS_M & PC_M & RC_L, R_H),       # Mid-part for low-res, good value
    ctrl.Rule(BS_M & PC_M & RC_M, R_E),       # Perfect Goldilocks match (Mid-range sweet spot)
    ctrl.Rule(BS_M & PC_M & RC_H, R_A),       # Borderline: Mid-part for high-res is generally weak

    # High Performance Priority
    ctrl.Rule(BS_M & PC_H & RC_L, R_E),       # Great value: High-part for low-res
    ctrl.Rule(BS_M & PC_H & RC_M, R_E),       # Optimal high-value setup (e.g., high-end 1440p)
    ctrl.Rule(BS_M & PC_H & RC_H, R_E),       # Optimal high-end value (e.g., high-end 4K)

    # --- 3. HIGH Budget (BS_H) Rules (9 Rules) ---
    # Low Performance Priority
    ctrl.Rule(BS_H & PC_L & RC_L, R_A),       # Waste of high budget on low perf part
    ctrl.Rule(BS_H & PC_L & RC_M, R_A),       # Waste of high budget on low perf part
    ctrl.Rule(BS_H & PC_L & RC_H, R_A),       # Waste of high budget on low perf part

    # Medium Performance Priority
    ctrl.Rule(BS_H & PC_M & RC_L, R_H),       # Safe choice for low res, but could have gotten better perf
    ctrl.Rule(BS_H & PC_M & RC_M, R_H),       # Safe choice for mid res
    ctrl.Rule(BS_H & PC_M & RC_H, R_H),       # Safe choice for high res, good part

    # High Performance Priority
    ctrl.Rule(BS_H & PC_H & RC_L, R_E),       # High-part for low-res, perfect result
    ctrl.Rule(BS_H & PC_H & RC_M, R_E),       # High-part for mid-res, perfect result
    ctrl.Rule(BS_H & PC_H & RC_H, R_E)        # Perfect high-end match (High budget, High perf, High res)
]

# -------------------------------------------------
# 4. Create Control System and Simulation
# -------------------------------------------------

reco_ctrl = ctrl.ControlSystem(rules)
reco_sim = ctrl.ControlSystemSimulation(reco_ctrl)

# -------------------------------------------------
# 5. Defuzzification and Simulation
#   Create a function to use the system
#   Takes the fuzzy output and converts back to a single, crisp number
# -------------------------------------------------

def get_reco_score(budget_value, perf_value, resolution_value):
    """
    Runs fuzzy simulation with given crisp values
    :param budget_value:
    :param perf_value:
    :param resolution_value:
    :return:
    """
    try:
        reco_sim.input['budget'] = budget_value
        reco_sim.input['performance_priority'] = perf_value
        reco_sim.input['preferred_resolution'] = resolution_value

        # Compute the result
        reco_sim.compute()

        # Extract defuzzified (crisp) output
        final_score = reco_sim.output['recommendation_score']
        return final_score

    except ValueError as e:
        print(f"Error during simulation while computing fuzzy logic: {e}. Check if inputs are within the defined universe.")
        return None

# ------------------------
# Graphs for display
# ------------------------
# budget.view()
# performance_priority.view()
# preferred_resolution.view()
# recommendation_score.view()
#
# plt.show()

# # --- Example Usage ---
# # Test Case 1: High budget, high performance, high resolution (4K)
# budget_d1 = 2800
# budget_n1 = normalize_budget(budget_d1)
# print(f"Case 1: High Budget (${budget_d1}) -> Normalized Score: {budget_n1:.2f}, High Performance, 4K Resolution")
# score1 = get_reco_score(budget_n1, 95, 95)
# print(f"Final Recommendation Score: {score1:.2f}\n")
#
# # Test Case 2: Medium budget, medium performance, medium resolution (1440p)
# budget_d2 = 1750
# budget_n2 = normalize_budget(budget_d2)
# print(f"Case 2: Medium Budget (${budget_d2}) -> Normalized Score: {budget_n2:.2f}, Medium Performance, 1440p Resolution")
# score2 = get_reco_score(50, 50, 50)
# print(f"Final Recommendation Score: {score2:.2f}\n")
#
# # Test Case 3: Low budget, low performance, but high resolution (4K)
# budget_d3 = 800
# budget_n3 = normalize_budget(budget_d3)
# print(f"Case 3: Low Budget (${budget_d3}) -> Normalized Score: {budget_n3:.2f}, Low Performance, 4K Resolution")
# score3 = get_reco_score(25, 30, 90)
# print(f"Final Recommendation Score: {score3:.2f}\n")
#
# # Test Case 4: Low budget, low performance, low resolution (1080p)
# budget_d4 = 500
# budget_n4 = normalize_budget(budget_d4)
# print(f"Case 4: Low Budget (${budget_d4}) -> Normalized Score: {budget_n4:.2f}, Low Performance, 1080p Resolution")
# score4 = get_reco_score(25, 30, 10)
# print(f"Final Recommendation Score: {score4:.2f}\n")

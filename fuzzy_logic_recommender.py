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

# Input Variables (Antecedent)
budget = ctrl.Antecedent(np.arange(0, 101, 1), 'budget')
performance_priority = ctrl.Antecedent(np.arange(0, 101, 1), 'performance_priority')
preferred_resolution = ctrl.Antecedent(np.arange(0, 101, 1), 'preferred_resolution')

# Output variable (Consequent)
# Will be the recommendation score for a given part, from 0 to 100
recommendation_score = ctrl.Consequent(np.arange(0, 101, 1), 'recommendation_score')


# -------------------------------------------------
# 2. Define Membership Functions (Fuzzy Sets)
#       Create Membership Functions for each variable
#       Using triangular membership functions for simplicity
#       Parameters are [start, peak, end] of the triangle
# -------------------------------------------------

# Budget
budget['low'] = fuzz.trimf(budget.universe, [0, 0, 50])
budget['medium'] = fuzz.trimf(budget.universe, [0, 50, 100])
budget['high'] = fuzz.trimf(budget.universe, [50, 100, 100])

# Performance Priority
performance_priority['low'] = fuzz.trimf(performance_priority.universe, [0, 0, 50])
performance_priority['medium'] = fuzz.trimf(performance_priority.universe, [0, 50, 100])
performance_priority['high'] = fuzz.trimf(performance_priority.universe, [50, 100, 100])

# resolution Priority
preferred_resolution['low'] = fuzz.trimf(preferred_resolution.universe, [0, 0, 50])
preferred_resolution['medium'] = fuzz.trimf(preferred_resolution.universe, [0, 50, 100])
preferred_resolution['high'] = fuzz.trimf(preferred_resolution.universe, [50, 100, 100])

# Recommendation Score (Output)
recommendation_score['low'] = fuzz.trimf(recommendation_score.universe, [0, 0, 50])
recommendation_score['medium'] = fuzz.trimf(recommendation_score.universe, [0, 50, 100])
recommendation_score['high'] = fuzz.trimf(recommendation_score.universe, [50, 100, 100])

# -------------------------------------------------
# 3. Define the Fuzzy Rules (The Knowledge Base)
#   Defining a set of IF-THEN rules that link
#       the inputs to the desired output.
#   Example: IF budget is high AND performance is high, THEN the recommendation score is high
# -------------------------------------------------

rules = [
    # High-end build rules
    ctrl.Rule(budget['high'] & performance_priority['high'], recommendation_score['high']),
    ctrl.Rule(budget['high'] & preferred_resolution['high'], recommendation_score['high']),

    # Medium build rules
    ctrl.Rule(budget['medium'] & performance_priority['medium'], recommendation_score['medium']),
    ctrl.Rule(budget['medium'] & preferred_resolution['medium'], recommendation_score['medium']),
    ctrl.Rule(budget['medium'] & performance_priority['low'] & preferred_resolution['low'], recommendation_score['low']),

    # Budget-focused rules
    ctrl.Rule(budget['low'] & performance_priority['high'], recommendation_score['medium']),
    ctrl.Rule(budget['low'] & performance_priority['low'], recommendation_score['low']),
    ctrl.Rule(budget['low'] & preferred_resolution['high'], recommendation_score['medium']),

    # Performance-focused rules
    ctrl.Rule(performance_priority['high'], recommendation_score['high']),
    ctrl.Rule(performance_priority['medium'], recommendation_score['medium']),

    # resolution-focused rules
    ctrl.Rule(preferred_resolution['high'], recommendation_score['high']),
    ctrl.Rule(preferred_resolution['medium'], recommendation_score['medium']),
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
budget.view()
performance_priority.view()
preferred_resolution.view()
recommendation_score.view()

plt.show()


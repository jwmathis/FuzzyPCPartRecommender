import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# 1. Fuzzification (Defining Fuzzy Variables and Membership functions)
# Take crisp inputs and convert them into fuzzy sets.

# Input Variables (Antecedent)
budget = ctrl.Antecedent(np.arange(0, 101, 1), 'budget')
performance_priority = ctrl.Antecedent(np.arange(0, 101, 1), 'performance_priority')
preferred_resolution = ctrl.Antecedent(np.arange(0, 101, 1), 'preferred_resolution')

# Output variable (Consequent)
# Will be the recommendation score for a given part, from 0 to 100
recommendation_score = ctrl.Consequent(np.arange(0, 101, 1), 'recommendation_score')

# Create Membership Functions for each variable
# Using triangular membership functions for simplicity
# Parameters are [start, peak, end] of the triangle

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

# 2. Rule Evaluation
# Defining a set of IF-THEN rules that link
# the inputs to the desired output.
# Example: IF budget is high AND performance is high, THEN the recommendation score is high

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

# Create the Fuzzy Control System
reco_ctrl = ctrl.ControlSystem(rules)
reco_sim = ctrl.ControlSystemSimulation(reco_ctrl)

# 3. Defuzzification and Simulation
# Create a function to use the system
# Takes the fuzzy output and converts back to a single, crip number

def get_reco_score(budget_value, perf_value, resolution_value):
    try:
        reco_sim.input['budget'] = budget_value
        reco_sim.input['performance_priority'] = perf_value
        reco_sim.input['preferred_resolution'] = resolution_value

        reco_sim.compute()

        final_score = reco_sim.output['recommendation_score']
        return final_score
    except ValueError as e:
        print(f"Error computing fuzzy logic: {e}")
        return None

# --- Example Usage ---
# Test Case 1: High budget, high performance, high resolution (4K)
print("Case 1: High Budget, High Performance, 4K Resolution")
score1 = get_reco_score(90, 95, 95)
print(f"Final Recommendation Score: {score1:.2f}\n")

# Test Case 2: Medium budget, medium performance, medium resolution (1440p)
print("Case 2: Medium Budget, Medium Performance, 1440p Resolution")
score2 = get_reco_score(50, 50, 50)
print(f"Final Recommendation Score: {score2:.2f}\n")

# Test Case 3: Low budget, low performance, but high resolution (4K)
print("Case 3: Low Budget, Low Performance, 4K Resolution")
score3 = get_reco_score(25, 30, 90)
print(f"Final Recommendation Score: {score3:.2f}\n")

# Test Case 4: Low budget, low performance, low resolution (1080p)
print("Case 4: Low Budget, Low Performance, 1080p Resolution")
score4 = get_reco_score(25, 30, 10)
print(f"Final Recommendation Score: {score4:.2f}\n")

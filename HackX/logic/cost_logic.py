def attach_costs(hospitals, cost_df, symptoms):
    hospitals = hospitals.copy()

    # ----------------------------
    # Base cost per symptom (₹)
    # ----------------------------
    symptom_base_cost = {
        "Chest Pain": 8000,
        "Breathing Difficulty": 7000,
        "Fracture": 6000,
        "Fever": 2000,
        "Headache": 1500
    }

    # ----------------------------
    # Compute base cost from symptoms
    # ----------------------------
    costs = [symptom_base_cost.get(s, 2000) for s in symptoms]

    if not costs:
        base_cost = 2000
    else:
        base_cost = max(costs)
        # Add 25% for each additional symptom
        base_cost += 0.25 * base_cost * (len(costs) - 1)

    # ----------------------------
    # Assign hospital-wise cost
    # ----------------------------
    def estimate(row):
        if row["ownership"] == "Government":
            return int(base_cost * 0.5)   # govt subsidized
        else:
            return int(base_cost * 1.5)   # private premium

    hospitals["estimated_cost"] = hospitals.apply(estimate, axis=1)

    return hospitals

import joblib
import numpy as np

# Dummy severity mapping (should match symptoms.csv)
SYMPTOM_SEVERITY = {
    "Chest Pain": 9,
    "Breathing Difficulty": 10,
    "Fever": 4,
    "Fracture": 8,
    "Headache": 3,
    "Abdominal Pain": 6
}

def extract_features(age, symptoms):
    if not symptoms:
        # No symptoms → lowest risk baseline
        return np.array([[age, 0, 0]])

    severities = [SYMPTOM_SEVERITY.get(s, 3) for s in symptoms]

    return np.array([
        age,
        sum(severities),
        max(severities)
    ]).reshape(1, -1)


def predict_risk(age, symptoms):
    severity_map = {
        "Chest Pain": 8,
        "Breathing Difficulty": 7,
        "Fracture": 6,
        "Fever": 3,
        "Headache": 2
    }

    score = age * 0.2
    for s in symptoms:
        score += severity_map.get(s, 1)

    if score >= 20:
        return "High"
    elif score >= 12:
        return "Medium"
    else:
        return "Low"



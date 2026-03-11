SYMPTOM_TO_SPECIALIZATION = {
    "Chest Pain": ["Cardiology"],
    "Breathing Difficulty": ["Pulmonology"],
    "Fracture": ["Orthopedics"],
    "Fever": ["General Medicine"],
    "Headache": ["General Medicine"]
}


def get_required_specializations(symptoms):
    specializations = set()
    for s in symptoms:
        specializations.update(SYMPTOM_TO_SPECIALIZATION.get(s, []))
    return list(specializations)

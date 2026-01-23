def attach_insurance(hospitals, policy, insurance_df, hosp_ins_df, condition):
    hospitals = hospitals.copy()

    # Default values
    hospitals["insurance_score"] = 0.0
    hospitals["insurance_status"] = "Not Considered"

    # If user has no insurance, return safely
    if policy == "No Insurance":
        hospitals["insurance_status"] = "No Insurance"
        return hospitals

    # If user selected ANY insurance, give soft preference
    hospitals["insurance_score"] = 0.2
    hospitals["insurance_status"] = "Insurance Selected"

    return hospitals

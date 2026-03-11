import os
import pandas as pd

# Resolve data directory relative to this file so it works
# no matter where the app is launched from.
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Load data once
USER_POLICY = pd.read_csv(os.path.join(DATA_DIR, "user_policy.csv"))
POLICY_MASTER = pd.read_csv(os.path.join(DATA_DIR, "policy_master.csv"))
INSURANCE_NETWORK = pd.read_csv(os.path.join(DATA_DIR, "insurance_network.csv"))

def get_user_policy(user_id, policy_name):
    if policy_name == "No Insurance":
        return None

    policy = USER_POLICY[
        (USER_POLICY["user_id"] == user_id) &
        (USER_POLICY["policy_name"] == policy_name)
    ]

    if policy.empty:
        return None

    return policy.iloc[0].to_dict()

def get_policy_rules(insurer, policy_name):
    rules = POLICY_MASTER[
        (POLICY_MASTER["insurer"] == insurer) &
        (POLICY_MASTER["policy_name"] == policy_name)
    ]

    if rules.empty:
        return None

    return rules.iloc[0].to_dict()

def is_hospital_in_network(insurer, hospital_name):
    return not INSURANCE_NETWORK[
        (INSURANCE_NETWORK["insurer"] == insurer) &
        (INSURANCE_NETWORK["hospital_name"] == hospital_name)
    ].empty

def insurance_decision(
    user_id,
    selected_policy_name,
    hospital_name,
    estimated_cost,
    requires_icu=False
):
    # 1️⃣ Policy selected?
    user_policy = get_user_policy(user_id, selected_policy_name)
    if user_policy is None:
        return {
            "status": "OUT_OF_POCKET",
            "reason": "No insurance policy selected"
        }

    # 2️⃣ Get policy rules
    policy_rules = get_policy_rules(
        user_policy["insurer"],
        user_policy["policy_name"]
    )

    if policy_rules is None:
        return {
            "status": "OUT_OF_POCKET",
            "reason": "Policy rules not found"
        }

    # 3️⃣ Hospital network check
    in_network = is_hospital_in_network(
        user_policy["insurer"],
        hospital_name
    )

    if not in_network:
        return {
            "status": "PARTIAL",
            "reason": "Hospital not in insurance network"
        }

    # 4️⃣ ICU logic
    if requires_icu and policy_rules["icu_covered"] != "Yes":
        return {
            "status": "PARTIAL",
            "reason": "ICU not covered under policy"
        }

    # 5️⃣ Coverage check
    if estimated_cost > policy_rules["max_coverage"]:
        return {
            "status": "PARTIAL",
            "reason": "Estimated cost exceeds coverage"
        }

    # ✅ Cashless
    return {
        "status": "CASHLESS",
        "reason": "Hospital & treatment covered under policy"
    }

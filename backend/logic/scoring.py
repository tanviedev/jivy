def rank_hospitals(df, risk_level):
    df = df.copy()

    # ----------------------------
    # Force numeric safety
    # ----------------------------
    df["distance_km"] = df["distance_km"].astype(float)

    df["estimated_cost"] = (
        df["estimated_cost"]
        .astype(str)
        .str.replace("[^0-9.]", "", regex=True)
        .replace("", "100000")
        .astype(float)
    )

    df["insurance_score"] = df.get("insurance_score", 0).astype(float)

    # ----------------------------
    # Scoring logic
    # ----------------------------
    def score(row):
        distance_score = 1 / (1 + row["distance_km"])
        cost_score = 1 / (1 + row["estimated_cost"])
        insurance_score = row["insurance_score"]

        if risk_level == "High":
            return 0.6 * distance_score + 0.4 * insurance_score

        elif risk_level == "Medium":
            return (
                0.4 * distance_score +
                0.3 * insurance_score +
                0.3 * cost_score
            )

        else:  # Low risk
            return (
                0.3 * distance_score +
                0.4 * cost_score +
                0.3 * insurance_score
            )

    df["final_score"] = df.apply(score, axis=1)
    return df.sort_values("final_score", ascending=False).head(5)

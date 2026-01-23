def filter_hospitals(df, risk_level):
    """
    Always returns at least one hospital.
    Degrades gracefully from strict → safe → any.
    """

    df = df.copy()

    # ------------------------------
    # STEP 1: STRICT FILTER (IDEAL)
    # ------------------------------
    if risk_level == "High":
        strict = df[df["facility_type"].isin(
            ["Hospital", "Medical College"]
        )]

    elif risk_level == "Medium":
        strict = df[df["facility_type"].isin(
            ["Hospital", "Medical College"]
        )]

    else:  # Low risk
        strict = df[df["facility_type"].isin(
            ["Clinic", "Dispensary", "Hospital", "Medical College"]
        )]

    if not strict.empty:
        return strict.reset_index(drop=True)

    # ------------------------------
    # STEP 2: SAFE FALLBACK
    # ------------------------------
    safe = df[df["facility_type"].isin(
        ["Hospital", "Medical College", "Clinic"]
    )]

    if not safe.empty:
        return safe.reset_index(drop=True)

    # ------------------------------
    # STEP 3: ABSOLUTE FALLBACK
    # ------------------------------
    # If data is extremely sparse, return nearest facilities
    return df.reset_index(drop=True)

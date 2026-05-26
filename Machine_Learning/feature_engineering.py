# Machine_Learning/feature_engineering.py

import pandas as pd
import numpy as np


# =========================================================
# SINGLE SOURCE OF TRUTH FEATURE ENGINEERING
# =========================================================
def create_features(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # -----------------------------
    # SAFE BOOLEAN CONVERSION
    # -----------------------------
    bool_cols = [
        "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen",
        "fifteen", "sixteen"
    ]

    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)
        else:
            df[col] = 0  # ensure column always exists

    # -----------------------------
    # FEATURE 1: people per room
    # -----------------------------
    if "one" not in df.columns:
        df["one"] = 0
    if "three" not in df.columns:
        df["three"] = 1  # avoid division issue

    df["people_per_room"] = df["one"] / df["three"].replace(0, 1)

    # -----------------------------
    # FEATURE 2: vacation factor
    # -----------------------------
    if "eighteen" not in df.columns:
        df["eighteen"] = 0

    df["vacation_factor"] = df["eighteen"] * 0.1

    # -----------------------------
    # FEATURE 3: appliance score
    # -----------------------------
    appliance_cols = [
        "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen"
    ]

    df["appliance_score"] = 0
    for col in appliance_cols:
        df["appliance_score"] += df[col]

    # -----------------------------
    # FEATURE 4: luxury score
    # -----------------------------
    df["luxury_score"] = df.get("fifteen", 0) + df.get("sixteen", 0)

    # -----------------------------
    # FEATURE 5: interaction feature
    # -----------------------------
    df["density_appliance_interaction"] = (
        df["people_per_room"] * df["appliance_score"]
    )

    # -----------------------------
    # CLEANUP (IMPORTANT)
    # -----------------------------
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)

    return df
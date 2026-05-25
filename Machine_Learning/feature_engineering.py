# Machine_Learning/feature_engineering.py

import pandas as pd
import numpy as np


def create_features(df: pd.DataFrame) -> pd.DataFrame:

    # -----------------------------
    # SAFETY: convert to numeric (VERY IMPORTANT)
    # -----------------------------
    bool_cols = [
        "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen",
        "fifteen", "sixteen"
    ]

    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(int)

    # -----------------------------
    # FEATURE 1: people per room
    # avoid division errors
    # -----------------------------
    if "one" in df.columns and "three" in df.columns:
        df["people_per_room"] = df["one"] / (df["three"].replace(0, 1))

    else:
        df["people_per_room"] = 0


    # -----------------------------
    # FEATURE 2: vacation factor
    # -----------------------------
    if "eighteen" in df.columns:
        df["vacation_factor"] = df["eighteen"] * 0.1
    else:
        df["vacation_factor"] = 0


    # -----------------------------
    # FEATURE 3: appliance score
    # (energy-heavy usage indicator)
    # -----------------------------
    appliance_cols = [
        "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen"
    ]

    df["appliance_score"] = 0
    for col in appliance_cols:
        if col in df.columns:
            df["appliance_score"] += df[col]


    # -----------------------------
    # FEATURE 4: luxury score
    # -----------------------------
    luxury_cols = ["fifteen", "sixteen"]

    df["luxury_score"] = 0
    for col in luxury_cols:
        if col in df.columns:
            df["luxury_score"] += df[col]


    # -----------------------------
    # FEATURE 5: interaction feature (IMPORTANT IMPROVEMENT)
    # -----------------------------
    if "people_per_room" in df.columns:
        df["density_appliance_interaction"] = (
            df["people_per_room"] * df["appliance_score"]
        )
    else:
        df["density_appliance_interaction"] = 0


    # -----------------------------
    # CLEANUP: NaN handling
    # -----------------------------
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)

    return df
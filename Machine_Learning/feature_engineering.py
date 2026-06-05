# Machine_Learning/feature_engineering.py

import pandas as pd
import numpy as np


# =========================================================
# GLOBAL FEATURE CONTRACT (IMPORTANT FIX)
# =========================================================
COMMON_NUMERIC_FEATURES = [
    "num_people",
    "num_children",
    "bedrooms",
    "home_area",
    "vacation_days",
    "year",
    "month",
]

COMMON_BOOL_FEATURES = [
    "has_ac",
    "has_geyser",
    "has_iron",
    "has_washing_machine",
    "has_dishwasher",
    "has_induction",
    "has_microwave",
    "has_kettle",
    "has_vacuum",
    "has_room_heater",
    "has_pool",
    "has_garden",
]


# =========================================================
# SAFE BOOLEAN CONVERSION (FIXED)
# =========================================================
def safe_bool_series(series: pd.Series):
    if series is None:
        return pd.Series(0)

    return series.fillna(0).apply(
        lambda x: 1 if str(x).strip().lower() in ["true", "1", "yes", "y", "on"] else 0
    )


# =========================================================
# CLIMATE ENCODING
# =========================================================
def encode_climate_series(series: pd.Series):
    mapping = {"cold": 0, "moderate": 1, "hot": 2}

    return series.fillna("moderate").apply(
        lambda x: mapping.get(str(x).strip().lower(), 1)
    )


# =========================================================
# MONTH FEATURES (CYCLICAL)
# =========================================================
def add_month_features(df: pd.DataFrame):
    df = df.copy()

    df["month"] = pd.to_numeric(df.get("month", 1), errors="coerce").fillna(1)

    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    return df


# =========================================================
# MAIN FEATURE ENGINEERING PIPELINE (FIXED + STABLE)
# =========================================================
def create_features(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # -----------------------------------------------------
    # NUMERIC FEATURES (SAFE)
    # -----------------------------------------------------
    for col in COMMON_NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0)

    # -----------------------------------------------------
    # BOOLEAN FEATURES (SAFE SERIES-BASED FIX)
    # -----------------------------------------------------
    for col in COMMON_BOOL_FEATURES:
        df[col] = safe_bool_series(df.get(col, pd.Series(0)))

    # -----------------------------------------------------
    # CLIMATE ENCODING
    # -----------------------------------------------------
    df["climate"] = encode_climate_series(df.get("climate", pd.Series(["moderate"] * len(df))))

    # -----------------------------------------------------
    # SAFE DIVISION FIX
    # -----------------------------------------------------
    df["bedrooms_safe"] = df["bedrooms"].replace(0, 1)
    df["people_safe"] = df["num_people"].replace(0, 1)

    df["people_per_room"] = df["num_people"] / df["bedrooms_safe"]
    df["children_ratio"] = df["num_children"] / df["people_safe"]

    # -----------------------------------------------------
    # CORE AGGREGATES (STABLE FEATURES)
    # -----------------------------------------------------
    df["appliance_score"] = df[COMMON_BOOL_FEATURES].sum(axis=1)

    df["luxury_score"] = df["has_pool"] + df["has_garden"]

    df["vacation_log"] = np.log1p(df["vacation_days"])

    df["area_per_person"] = df["home_area"] / df["people_safe"]

    # -----------------------------------------------------
    # RISK SCORE (SIMPLIFIED + STABLE)
    # -----------------------------------------------------
    df["consumption_risk"] = (
        df["appliance_score"]
        + df["luxury_score"]
        + df["climate"]
        + df["people_per_room"]
    )

    # -----------------------------------------------------
    # CYCLICAL FEATURES
    # -----------------------------------------------------
    df = add_month_features(df)

    # -----------------------------------------------------
    # SAFE FINAL CLEANUP
    # -----------------------------------------------------
    df = df.replace([np.inf, -np.inf], 0)
    df = df.fillna(0)

    return df
# Machine_Learning/feature_engineering.py
import pandas as pd
import numpy as np


# =========================================================
# SAFE BOOLEAN CONVERSION
# =========================================================
def safe_bool(value):
    if pd.isna(value):
        return 0

    if isinstance(value, str):
        return 1 if value.lower() in ["true", "1", "yes", "y"] else 0

    return int(bool(value))


# =========================================================
# SAFE CLIMATE ENCODING
# =========================================================
def encode_climate(value):
    climate_map = {
        "cold": 0,
        "moderate": 1,
        "hot": 2,
    }

    if pd.isna(value):
        return 1

    return climate_map.get(str(value).lower(), 1)


# =========================================================
# CYCLICAL MONTH ENCODING
# =========================================================
def add_month_cyclical_features(df: pd.DataFrame):
    df = df.copy()

    if "month" not in df.columns:
        df["month"] = 1

    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    return df


# =========================================================
# MAIN FEATURE ENGINEERING PIPELINE (LEAKAGE SAFE)
# =========================================================
def create_features(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # =====================================================
    # BOOLEAN COLUMNS
    # =====================================================
    bool_cols = [
        "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve",
        "thirteen", "fifteen", "sixteen"
    ]

    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].apply(safe_bool)
        else:
            df[col] = 0

    # =====================================================
    # NUMERIC COLUMNS
    # =====================================================
    numeric_defaults = {
        "one": 1,
        "two": 0,
        "three": 1,
        "fourteen": 0,
        "eighteen": 0,
        "month": 1,
        "year": 2025,
    }

    for col, default in numeric_defaults.items():
        if col not in df.columns:
            df[col] = default

        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default)

    # =====================================================
    # CLIMATE ENCODING
    # =====================================================
    if "nineteen" in df.columns:
        df["nineteen"] = df["nineteen"].apply(encode_climate)
    else:
        df["nineteen"] = 1

    # =====================================================
    # SAFE FEATURE ENGINEERING
    # =====================================================

    # People density
    df["people_per_room"] = df["one"] / df["three"].replace(0, 1)

    # Children ratio
    df["children_ratio"] = df["two"] / df["one"].replace(0, 1)

    # Vacation impact (simple scaling only)
    df["vacation_factor"] = df["eighteen"] * 0.1

    # Appliance usage score
    appliance_cols = [
        "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen"
    ]

    df["appliance_score"] = df[appliance_cols].sum(axis=1)

    # Luxury score
    df["luxury_score"] = df["fifteen"] + df["sixteen"]

    # Area per person
    df["area_per_person"] = df["fourteen"] / df["one"].replace(0, 1)

    # =====================================================
    # SAFE INTERACTIONS (NO TARGET LEAKAGE)
    # =====================================================

    df["density_appliance_interaction"] = (
        df["people_per_room"] * df["appliance_score"]
    )

    df["climate_appliance_interaction"] = (
        df["nineteen"] * df["appliance_score"]
    )

    df["area_appliance_interaction"] = (
        df["area_per_person"] * df["appliance_score"]
    )

    # =====================================================
    # SIMPLIFIED RISK SCORE (NO HARD WEIGHTS)
    # =====================================================
    df["high_consumption_risk"] = (
        df["appliance_score"] +
        df["luxury_score"] +
        df["nineteen"] +
        df["people_per_room"]
    )

    # =====================================================
    # CYCLICAL FEATURES
    # =====================================================
    df = add_month_cyclical_features(df)

    # =====================================================
    # IMPORTANT FIX:
    # REMOVE TARGET-BASED FEATURES (LEAKAGE FIX)
    # =====================================================
    leakage_cols = [
        "consumption_growth_rate",
        "last_month_consumption",
        "avg_last_3_months",
        "avg_last_6_months",
        "yearly_avg_consumption",
        "max_historical_consumption",
        "min_historical_consumption",
    ]

    for col in leakage_cols:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)

    # =====================================================
    # FINAL CLEANUP
    # =====================================================
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)

    return df
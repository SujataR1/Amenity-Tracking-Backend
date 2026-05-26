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
        return 1 if value.strip().lower() in ["true", "1", "yes", "y", "on"] else 0

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

    return climate_map.get(str(value).strip().lower(), 1)


# =========================================================
# CYCLICAL MONTH ENCODING
# =========================================================
def add_month_cyclical_features(df: pd.DataFrame):

    df = df.copy()

    if "month" not in df.columns:
        df["month"] = 1

    df["month"] = pd.to_numeric(df["month"], errors="coerce").fillna(1)

    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    return df


# =========================================================
# MAIN FEATURE ENGINEERING PIPELINE (UPDATED FOR NEW SCHEMA)
# =========================================================
def create_features(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # =====================================================
    # BOOLEAN COLUMNS (UPDATED TO NEW BACKEND SCHEMA)
    # =====================================================
    bool_cols = [
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

    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].apply(safe_bool)
        else:
            df[col] = 0

    # =====================================================
    # NUMERIC COLUMNS (NEW SCHEMA)
    # =====================================================
    numeric_defaults = {
        "num_people": 1,
        "num_children": 0,
        "bedrooms": 1,
        "home_area": 0,
        "vacation_days": 0,
        "month": 1,
        "year": 2025,
    }

    for col, default in numeric_defaults.items():

        if col not in df.columns:
            df[col] = default

        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default)

    # =====================================================
    # CLIMATE ENCODING (NEW COLUMN NAME)
    # =====================================================
    if "climate" in df.columns:
        df["climate"] = df["climate"].apply(encode_climate)
    else:
        df["climate"] = 1

    # =====================================================
    # ENGINEERED FEATURES (UPDATED LOGIC)
    # =====================================================

    df["people_per_room"] = df["num_people"] / df["bedrooms"].replace(0, 1)

    df["children_ratio"] = df["num_children"] / df["num_people"].replace(0, 1)

    df["vacation_factor"] = df["vacation_days"] * 0.1

    appliance_cols = [
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
    ]

    df["appliance_score"] = df[appliance_cols].sum(axis=1)

    df["luxury_score"] = df["has_pool"] + df["has_garden"]

    df["area_per_person"] = df["home_area"] / df["num_people"].replace(0, 1)

    # =====================================================
    # INTERACTIONS (SAFE, NO LEAKAGE)
    # =====================================================

    df["density_appliance_interaction"] = (
        df["people_per_room"] * df["appliance_score"]
    )

    df["climate_appliance_interaction"] = (
        df["climate"] * df["appliance_score"]
    )

    df["area_appliance_interaction"] = (
        df["area_per_person"] * df["appliance_score"]
    )

    # =====================================================
    # RISK SCORE (HEURISTIC FEATURE)
    # =====================================================

    df["high_consumption_risk"] = (
        df["appliance_score"] +
        df["luxury_score"] +
        df["climate"] +
        df["people_per_room"]
    )

    # =====================================================
    # CYCLICAL FEATURES
    # =====================================================
    df = add_month_cyclical_features(df)

    # =====================================================
    # CLEANUP
    # =====================================================
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)

    return df
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
    mapping = {
        "cold": 0,
        "moderate": 1,
        "hot": 2,
    }

    if pd.isna(value):
        return 1

    return mapping.get(str(value).strip().lower(), 1)


# =========================================================
# MONTH CYCLICAL ENCODING
# =========================================================
def add_month_features(df: pd.DataFrame):

    df = df.copy()

    df["month"] = pd.to_numeric(df.get("month", 1), errors="coerce").fillna(1)

    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    return df


# =========================================================
# MAIN FEATURE ENGINEERING
# =========================================================
def create_features(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # -----------------------------------------------------
    # BOOLEAN FEATURES
    # -----------------------------------------------------
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
        df[col] = df.get(col, 0).apply(safe_bool)

    # -----------------------------------------------------
    # NUMERIC FEATURES
    # -----------------------------------------------------
    numeric_defaults = {
        "num_people": 1,
        "num_children": 0,
        "bedrooms": 1,
        "home_area": 0,
        "vacation_days": 0,
        "year": 2025,
        "month": 1,
    }

    for col, default in numeric_defaults.items():
        df[col] = pd.to_numeric(df.get(col, default), errors="coerce").fillna(default)

    # -----------------------------------------------------
    # CLIMATE
    # -----------------------------------------------------
    df["climate"] = df.get("climate", "moderate").apply(encode_climate)

    # -----------------------------------------------------
    # SAFE DIVISION FIX (IMPORTANT)
    # -----------------------------------------------------
    df["bedrooms_safe"] = df["bedrooms"].replace(0, 1)
    df["num_people_safe"] = df["num_people"].replace(0, 1)

    df["people_per_room"] = df["num_people"] / df["bedrooms_safe"]
    df["children_ratio"] = df["num_children"] / df["num_people_safe"]

    # -----------------------------------------------------
    # TRANSFORMATIONS
    # -----------------------------------------------------
    df["vacation_factor"] = np.log1p(df["vacation_days"])

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

    df["area_per_person"] = df["home_area"] / df["num_people_safe"]

    # -----------------------------------------------------
    # INTERACTIONS
    # -----------------------------------------------------
    df["density_x_appliance"] = df["people_per_room"] * df["appliance_score"]

    df["area_x_appliance"] = df["area_per_person"] * df["appliance_score"]

    df["climate_x_appliance"] = df["climate"] * df["appliance_score"]

    # -----------------------------------------------------
    # RISK SCORE
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
    # FINAL CLEANUP (CRITICAL FIX)
    # -----------------------------------------------------
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)

    return df
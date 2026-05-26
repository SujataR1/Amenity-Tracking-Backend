# Machine_Learning/preprocessing.py

import pandas as pd
import numpy as np


# =========================================================
# SAFE BOOLEAN CONVERSION
# =========================================================
def convert_boolean(value):

    if pd.isna(value):
        return 0

    if isinstance(value, str):
        value = value.strip().lower()
        return 1 if value in ["true", "1", "yes", "y", "on"] else 0

    return 1 if bool(value) else 0


# =========================================================
# SAFE CLIMATE CONVERSION
# =========================================================
def convert_climate(climate):

    if pd.isna(climate):
        return 1

    climate = str(climate).strip().lower()

    climate_mapping = {
        "cold": 0,
        "moderate": 1,
        "hot": 2,
    }

    return climate_mapping.get(climate, 1)


# =========================================================
# SAFE NUMERIC CONVERSION
# =========================================================
def convert_numeric(series, default_value=0):
    return pd.to_numeric(series, errors="coerce").fillna(default_value)


# =========================================================
# MAIN PREPROCESSING PIPELINE (UPDATED FOR NEW SCHEMA)
# =========================================================
def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # =====================================================
    # BOOLEAN COLUMNS (UPDATED TO NEW BACKEND SCHEMA)
    # =====================================================
    boolean_columns = [
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

    for col in boolean_columns:
        if col in df.columns:
            df[col] = df[col].apply(convert_boolean)
        else:
            df[col] = 0

    # =====================================================
    # NUMERIC COLUMNS (UPDATED SCHEMA)
    # =====================================================
    numeric_columns = {
        "num_people": 0,
        "num_children": 0,
        "bedrooms": 1,
        "home_area": 0,
        "vacation_days": 0,
        "billing_days": 30,
        "month": 1,
        "year": 2025,
    }

    for col, default_value in numeric_columns.items():

        if col not in df.columns:
            df[col] = default_value

        df[col] = convert_numeric(df[col], default_value)

    # =====================================================
    # CLIMATE COLUMN
    # =====================================================
    if "climate" in df.columns:
        df["climate"] = df["climate"].apply(convert_climate)
    else:
        df["climate"] = 1

    # =====================================================
    # TARGET SAFETY (TRAINING ONLY)
    # =====================================================
    target_cols = ["electricity_consumption", "bill_amount"]

    for col in target_cols:
        if col in df.columns:
            df[col] = convert_numeric(df[col], 0)

    # =====================================================
    # NON-NEGATIVE SAFETY RULE
    # =====================================================
    non_negative_columns = [
        "num_people",
        "num_children",
        "bedrooms",
        "home_area",
        "vacation_days",
        "electricity_consumption",
        "bill_amount",
    ]

    for col in non_negative_columns:
        if col in df.columns:
            df[col] = df[col].clip(lower=0)

    # =====================================================
    # BILLING DAYS VALIDATION
    # =====================================================
    if "billing_days" in df.columns:
        df["billing_days"] = pd.to_numeric(df["billing_days"], errors="coerce").fillna(30)
        df["billing_days"] = df["billing_days"].clip(1, 365)

    # =====================================================
    # CLEANUP
    # =====================================================
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


# =========================================================
# TEST BLOCK
# =========================================================
if __name__ == "__main__":

    sample_data = {
        "num_people": [5],
        "num_children": [2],
        "bedrooms": [3],
        "has_ac": ["yes"],
        "has_geyser": [True],
        "has_washing_machine": ["false"],
        "home_area": [1500],
        "vacation_days": [10],
        "climate": ["hot"],
        "electricity_consumption": [420],
        "bill_amount": [3500],
        "billing_days": [30],
    }

    df = pd.DataFrame(sample_data)

    cleaned_df = preprocess_dataframe(df)

    print("\n========== CLEANED DATA ==========\n")
    print(cleaned_df)
    print("\n==================================\n")
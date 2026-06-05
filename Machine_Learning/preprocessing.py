# Machine_Learning/preprocessing.py

import pandas as pd
import numpy as np


# =========================================================
# GLOBAL CONSTANTS (SINGLE SOURCE OF TRUTH)
# =========================================================
BOOLEAN_MAP = {
    True: 1,
    False: 0,
}

CLIMATE_MAP = {
    "cold": 0,
    "moderate": 1,
    "hot": 2,
}

MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


# =========================================================
# BOOLEAN CONVERSION
# =========================================================
def convert_boolean(value):

    if pd.isna(value):
        return 0

    if value in BOOLEAN_MAP:
        return BOOLEAN_MAP[value]

    if isinstance(value, str):

        value = value.strip().lower()

        if value in ["true", "1", "yes", "y", "on"]:
            return 1

        if value in ["false", "0", "no", "n", "off"]:
            return 0

    return int(bool(value))


# =========================================================
# CLIMATE CONVERSION
# =========================================================
def convert_climate(value):

    if pd.isna(value):
        return 1

    value = str(value).strip().lower()

    return CLIMATE_MAP.get(value, 1)


# =========================================================
# MONTH ORDINAL ENCODING
# =========================================================
def convert_month(value):

    if pd.isna(value):
        return 1

    if isinstance(value, str):

        value = value.strip().lower()

        if value in MONTH_MAP:
            return MONTH_MAP[value]

    try:
        value = int(value)

        if 1 <= value <= 12:
            return value

    except Exception:
        pass

    return 1


# =========================================================
# NUMERIC CONVERSION
# =========================================================
def convert_numeric(series, default_value=0):

    return (
        pd.to_numeric(
            series,
            errors="coerce",
        )
        .fillna(default_value)
    )


# =========================================================
# MAIN PREPROCESSING PIPELINE
# =========================================================
def preprocess_dataframe(df: pd.DataFrame):

    df = df.copy()

    # =====================================================
    # BOOLEAN FEATURES
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

        "water_heating",
    ]

    for col in boolean_columns:

        if col not in df.columns:
            df[col] = 0

        df[col] = df[col].apply(convert_boolean)

    # =====================================================
    # NUMERIC FEATURES
    # =====================================================
    numeric_defaults = {

        "num_people": 1,
        "num_children": 0,
        "bedrooms": 1,

        "home_area": 0,

        "vacation_days": 0,

        "billing_days": 30,

        "vehicle_count": 0,
        "daily_distance_km": 0,

        "year": 2025,
    }

    for col, default in numeric_defaults.items():

        if col not in df.columns:
            df[col] = default

        df[col] = convert_numeric(
            df[col],
            default,
        )

    # =====================================================
    # MONTH ENCODING
    # =====================================================
    if "month" not in df.columns:
        df["month"] = 1

    df["month"] = df["month"].apply(convert_month)

    # =====================================================
    # CLIMATE ENCODING
    # =====================================================
    if "climate" not in df.columns:
        df["climate"] = "moderate"

    df["climate"] = df["climate"].apply(
        convert_climate
    )

    # =====================================================
    # TARGET CLEANING (ALL 4 MODELS)
    # =====================================================
    target_columns = [

        "electricity_consumption",
        "water_consumption",
        "gas_consumption",
        "fuel_consumption",

        "bill_amount",
    ]

    for col in target_columns:

        if col in df.columns:

            df[col] = convert_numeric(
                df[col],
                0,
            )

            df[col] = df[col].clip(
                lower=0
            )

    # =====================================================
    # NON NEGATIVE RULES
    # =====================================================
    clip_columns = [

        "num_people",
        "num_children",
        "bedrooms",

        "home_area",

        "vacation_days",

        "vehicle_count",

        "daily_distance_km",

        "billing_days",
    ]

    for col in clip_columns:

        if col in df.columns:

            df[col] = df[col].clip(
                lower=0
            )

    # =====================================================
    # BILLING DAYS VALIDATION
    # =====================================================
    if "billing_days" in df.columns:

        df["billing_days"] = (
            df["billing_days"]
            .clip(1, 365)
        )

    # =====================================================
    # FINAL CLEANUP
    # =====================================================
    df = (
        df
        .replace(
            [np.inf, -np.inf],
            0,
        )
        .fillna(0)
        .reset_index(
            drop=True
        )
    )

    return df


# =========================================================
# TEST
# =========================================================
if __name__ == "__main__":

    sample = pd.DataFrame({

        "num_people": [5],

        "has_ac": ["yes"],

        "month": ["June"],

        "climate": ["hot"],

        "electricity_consumption": [350],

    })

    result = preprocess_dataframe(sample)

    print(result)
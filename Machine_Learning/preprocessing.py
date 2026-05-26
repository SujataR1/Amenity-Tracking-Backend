# Machine_Learning/preprocessing.py

import pandas as pd
import numpy as np

from Questionnaire.Data_Schemas import ClimateEnum


# =========================================================
# SAFE BOOLEAN CONVERSION
# =========================================================
def convert_boolean(value):

    # -----------------------------------------------------
    # NULL SAFETY
    # -----------------------------------------------------
    if pd.isna(value):
        return 0

    # -----------------------------------------------------
    # STRING HANDLING
    # -----------------------------------------------------
    if isinstance(value, str):

        value = value.strip().lower()

        true_values = [
            "true",
            "1",
            "yes",
            "y",
            "on",
        ]

        return 1 if value in true_values else 0

    # -----------------------------------------------------
    # NORMAL BOOLEAN
    # -----------------------------------------------------
    return 1 if bool(value) else 0


# =========================================================
# SAFE CLIMATE CONVERSION
# =========================================================
def convert_climate(climate):

    # -----------------------------------------------------
    # NULL SAFETY
    # -----------------------------------------------------
    if pd.isna(climate):
        return 1

    # -----------------------------------------------------
    # NORMALIZE STRING
    # -----------------------------------------------------
    if isinstance(climate, str):
        climate = climate.strip().lower()

    # -----------------------------------------------------
    # CLIMATE MAP
    # -----------------------------------------------------
    climate_mapping = {

        # STRING VALUES
        "cold": 0,
        "moderate": 1,
        "hot": 2,

        # ENUM VALUES
        ClimateEnum.cold: 0,
        ClimateEnum.moderate: 1,
        ClimateEnum.hot: 2,
    }

    return climate_mapping.get(climate, 1)


# =========================================================
# SAFE NUMERIC CONVERSION
# =========================================================
def convert_numeric(
    series,
    default_value=0,
):

    return pd.to_numeric(
        series,
        errors="coerce",
    ).fillna(default_value)


# =========================================================
# MAIN PREPROCESSING PIPELINE
# =========================================================
def preprocess_dataframe(
    df: pd.DataFrame,
) -> pd.DataFrame:

    # -----------------------------------------------------
    # COPY DATAFRAME
    # -----------------------------------------------------
    df = df.copy()

    # =====================================================
    # BOOLEAN COLUMNS
    # =====================================================
    boolean_columns = [

        "four",
        "five",
        "six",
        "seven",
        "eight",

        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",

        "fifteen",
        "sixteen",
    ]

    for col in boolean_columns:

        if col in df.columns:

            df[col] = df[col].apply(
                convert_boolean
            )

        else:

            df[col] = 0

    # =====================================================
    # CLIMATE CLEANING
    # =====================================================
    if "nineteen" in df.columns:

        df["nineteen"] = df["nineteen"].apply(
            convert_climate
        )

    else:

        df["nineteen"] = 1

    # =====================================================
    # NUMERIC COLUMNS
    # =====================================================
    numeric_columns = {

        "one": 0,
        "two": 0,
        "three": 1,

        "fourteen": 0,

        "eighteen": 0,

        "month": 1,

        "year": 2025,

        "electricity_consumption": 0,

        "bill_amount": 0,

        "billing_days": 30,
    }

    for col, default_value in numeric_columns.items():

        if col not in df.columns:

            df[col] = default_value

        df[col] = convert_numeric(
            df[col],
            default_value=default_value,
        )

    # =====================================================
    # NEGATIVE VALUE PROTECTION
    # =====================================================
    non_negative_columns = [

        "one",
        "two",
        "three",

        "fourteen",

        "eighteen",

        "electricity_consumption",

        "bill_amount",

        "billing_days",
    ]

    for col in non_negative_columns:

        if col in df.columns:

            df[col] = df[col].clip(lower=0)

    # =====================================================
    # BILLING DAYS VALIDATION
    # =====================================================
    if "billing_days" in df.columns:

        df["billing_days"] = df[
            "billing_days"
        ].clip(
            lower=1,
            upper=365,
        )

    # =====================================================
    # FINAL CLEANUP
    # =====================================================
    df.replace(
        [np.inf, -np.inf],
        0,
        inplace=True,
    )

    df.fillna(
        0,
        inplace=True,
    )

    # =====================================================
    # RESET INDEX
    # =====================================================
    df.reset_index(
        drop=True,
        inplace=True,
    )

    return df


# =========================================================
# TESTING
# =========================================================
if __name__ == "__main__":

    sample_data = {

        "one": [5],

        "two": [2],

        "three": [3],

        "four": ["yes"],

        "five": [True],

        "six": ["false"],

        "fourteen": [1500],

        "eighteen": [10],

        "nineteen": ["hot"],

        "electricity_consumption": [420],

        "bill_amount": [3500],

        "billing_days": [30],
    }

    df = pd.DataFrame(sample_data)

    cleaned_df = preprocess_dataframe(df)

    print("\n========== CLEANED DATA ==========\n")

    print(cleaned_df)

    print("\n==================================\n")
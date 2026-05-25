# Machine_Learning/preprocessing.py

import pandas as pd
import numpy as np

from Questionnaire.Data_Schemas import ClimateEnum


# -----------------------------
# BOOLEAN SAFE CONVERSION
# -----------------------------
def convert_boolean(value):
    """
    Robust boolean conversion:
    Handles True/False, 1/0, "true"/"false", None
    """
    if pd.isna(value):
        return 0

    if isinstance(value, str):
        return 1 if value.lower() in ["true", "1", "yes", "y"] else 0

    return 1 if bool(value) else 0


# -----------------------------
# CLIMATE ENCODING
# -----------------------------
def convert_climate(climate):
    """
    Safe enum / string / numeric handling
    """
    if pd.isna(climate):
        return 1

    climate_mapping = {
        "hot": 2,
        "moderate": 1,
        "cold": 0,
        ClimateEnum.hot: 2,
        ClimateEnum.moderate: 1,
        ClimateEnum.cold: 0,
    }

    return climate_mapping.get(climate, 1)


# -----------------------------
# MAIN PREPROCESSING PIPELINE
# -----------------------------
def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    # -------------------------
    # REQUIRED BOOLEAN COLUMNS
    # -------------------------
    boolean_columns = [
        "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen",
        "fifteen", "sixteen"
    ]

    for column in boolean_columns:
        if column in df.columns:
            df[column] = df[column].apply(convert_boolean)
        else:
            df[column] = 0  # safety fallback

    # -------------------------
    # CLIMATE COLUMN
    # -------------------------
    if "nineteen" in df.columns:
        df["nineteen"] = df["nineteen"].apply(convert_climate)
    else:
        df["nineteen"] = 1


    # -------------------------
    # SAFETY: numeric coercion
    # -------------------------
    numeric_columns = df.columns

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")


    # -------------------------
    # CLEANING
    # -------------------------
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)

    return df
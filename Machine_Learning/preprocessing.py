# Machine_Learning/preprocessing.py

import pandas as pd
import numpy as np
from Questionnaire.Data_Schemas import ClimateEnum


# =========================================================
# SAFE BOOLEAN CONVERSION
# =========================================================
def convert_boolean(value):
    if pd.isna(value):
        return 0

    if isinstance(value, str):
        return 1 if value.lower() in ["true", "1", "yes", "y"] else 0

    return 1 if bool(value) else 0


# =========================================================
# SAFE CLIMATE CONVERSION
# =========================================================
def convert_climate(climate):

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


# =========================================================
# CLEANING PIPELINE (ONLY CLEANING - NO FEATURES)
# =========================================================
def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # -------------------------
    # BOOLEAN COLUMNS CLEANING
    # -------------------------
    boolean_columns = [
        "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen",
        "fifteen", "sixteen"
    ]

    for col in boolean_columns:
        if col in df.columns:
            df[col] = df[col].apply(convert_boolean)
        else:
            df[col] = 0

    # -------------------------
    # CLIMATE CLEANING
    # -------------------------
    if "nineteen" in df.columns:
        df["nineteen"] = df["nineteen"].apply(convert_climate)
    else:
        df["nineteen"] = 1

    # -------------------------
    # BASIC NUMERIC SAFETY
    # -------------------------
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    # -------------------------
    # FINAL CLEANUP
    # -------------------------
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)

    return df
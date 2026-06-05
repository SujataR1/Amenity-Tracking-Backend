# Machine_Learning/Methods.py

import pandas as pd
import numpy as np

from Database_and_ORM.Database_Models import (
    ElectricityConsumption,
    QuestionnaireAnswers,
    WaterConsumption,
    GasConsumption,
    FuelConsumption,
    User,
)

# =========================================================
# MODEL MAPPING (SAFE + EXTENSIBLE)
# =========================================================
MODEL_MAP = {
    "electricity": ElectricityConsumption,
    "water": WaterConsumption,
    "gas": GasConsumption,
    "fuel": FuelConsumption,
}


# =========================================================
# DATASET BUILDER (ONLY RESPONSIBILITY HERE)
# =========================================================
async def build_dataset(resource_type: str):

    if resource_type not in MODEL_MAP:
        raise ValueError(f"Invalid resource_type: {resource_type}")

    resource_model = MODEL_MAP[resource_type]

    users = await User.all().values("id")
    user_ids = [u["id"] for u in users]

    # -----------------------------
    # CONSUMPTION DATA
    # -----------------------------
    consumption = await resource_model.filter(
        user_id__in=user_ids
    ).values()

    # -----------------------------
    # QUESTIONNAIRE DATA
    # -----------------------------
    questionnaire = await QuestionnaireAnswers.filter(
        user_id__in=user_ids
    ).values()

    # Convert to DataFrames
    df_consumption = pd.DataFrame(consumption)
    df_questionnaire = pd.DataFrame(questionnaire)

    if df_consumption.empty:
        raise ValueError(f"No consumption data found for {resource_type}")

    # Merge datasets
    df = df_consumption.merge(
        df_questionnaire,
        on="user_id",
        how="left"
    )

    # Fill missing safely
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(0)

    return df


# =========================================================
# OPTIONAL UTILITY: SAFE SORTING (FOR EXTERNAL USE ONLY)
# =========================================================
def sort_by_time(df: pd.DataFrame):
    """
    Utility only — NO FEATURE CREATION HERE.
    Used by feature_engineering.py
    """
    if "year" in df.columns and "month" in df.columns:
        return df.sort_values(["user_id", "year", "month"])
    return df


# =========================================================
# REMOVE EVERYTHING ELSE
# =========================================================
# ❌ NO:
# - training logic
# - XGBoost
# - evaluation
# - feature engineering
# - historical features
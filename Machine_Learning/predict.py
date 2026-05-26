# Machine_Learning/predict.py

import json
import joblib
import pandas as pd
import numpy as np

from Machine_Learning.constants import (
    MODEL_PATH,
    FEATURES_PATH,
)

from Machine_Learning.preprocessing import preprocess_dataframe
from Machine_Learning.feature_engineering import create_features


# =========================================================
# BILL CALCULATION ENGINE
# =========================================================
def calculate_electricity_bill(units: float):

    units = max(units, 0)

    if units <= 100:
        bill = units * 5

    elif units <= 300:
        bill = (100 * 5) + ((units - 100) * 7)

    else:
        bill = (100 * 5) + (200 * 7) + ((units - 300) * 10)

    return round(float(bill), 2)


# =========================================================
# LOAD MODEL
# =========================================================
def load_model():
    return joblib.load(MODEL_PATH)


# =========================================================
# LOAD FEATURE NAMES
# =========================================================
def load_feature_names():

    with open(FEATURES_PATH, "r") as f:
        data = json.load(f)

    # supports both formats safely
    if isinstance(data, dict) and "features" in data:
        return data["features"]

    return data


# =========================================================
# PREPARE INPUT DATAFRAME (UPDATED SCHEMA)
# =========================================================
def prepare_input_dataframe(input_data: dict) -> pd.DataFrame:

    df = pd.DataFrame([input_data])

    # =====================================================
    # UPDATED DEFAULT SCHEMA (NEW BACKEND FIELDS)
    # =====================================================
    defaults = {
        "num_people": 0,
        "num_children": 0,
        "bedrooms": 1,
        "home_area": 0,

        "has_ac": 0,
        "has_geyser": 0,
        "has_iron": 0,
        "has_washing_machine": 0,
        "has_dishwasher": 0,
        "has_induction": 0,
        "has_microwave": 0,
        "has_kettle": 0,
        "has_vacuum": 0,
        "has_room_heater": 0,
        "has_pool": 0,
        "has_garden": 0,

        "vacation_days": 0,
        "climate": "moderate",

        "month": 1,
        "year": 2025,
    }

    for col, default_value in defaults.items():
        if col not in df.columns:
            df[col] = default_value

    return df


# =========================================================
# ALIGN FEATURES
# =========================================================
def align_features(df: pd.DataFrame, feature_names: list) -> pd.DataFrame:

    df = pd.get_dummies(df)

    df = df.reindex(columns=feature_names, fill_value=0)

    return df


# =========================================================
# MAIN PREDICTION FUNCTION
# =========================================================
def predict_consumption(input_data: dict):

    # -----------------------------------------------------
    # LOAD MODEL + FEATURES
    # -----------------------------------------------------
    model = load_model()
    feature_names = load_feature_names()

    # -----------------------------------------------------
    # BUILD INPUT
    # -----------------------------------------------------
    df = prepare_input_dataframe(input_data)

    # -----------------------------------------------------
    # PREPROCESS PIPELINE
    # -----------------------------------------------------
    df = preprocess_dataframe(df)
    df = create_features(df)

    # -----------------------------------------------------
    # ALIGN FEATURES (CRITICAL)
    # -----------------------------------------------------
    df = align_features(df, feature_names)

    # -----------------------------------------------------
    # PREDICTION
    # -----------------------------------------------------
    prediction_log = model.predict(df)[0]

    prediction = np.expm1(prediction_log)

    prediction = max(prediction, 0)

    # -----------------------------------------------------
    # BILL ESTIMATION
    # -----------------------------------------------------
    estimated_bill = calculate_electricity_bill(prediction)

    # -----------------------------------------------------
    # USAGE LEVEL
    # -----------------------------------------------------
    if prediction < 200:
        usage_level = "Low"
    elif prediction < 500:
        usage_level = "Moderate"
    else:
        usage_level = "High"

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------
    return {
        "predicted_electricity_consumption": round(float(prediction), 2),
        "estimated_bill_amount": round(float(estimated_bill), 2),
        "usage_level": usage_level,
    }


# =========================================================
# TESTING
# =========================================================
if __name__ == "__main__":

    sample_input = {
        "num_people": 5,
        "num_children": 2,
        "bedrooms": 3,

        "has_ac": True,
        "has_geyser": True,
        "has_washing_machine": True,
        "has_dishwasher": False,
        "has_induction": True,
        "has_microwave": True,
        "has_kettle": True,
        "has_vacuum": False,
        "has_room_heater": False,

        "home_area": 1400,
        "has_pool": False,
        "has_garden": True,

        "vacation_days": 10,
        "climate": "hot",

        "month": 6,
        "year": 2025,
    }

    result = predict_consumption(sample_input)

    print("\n========== PREDICTION ==========\n")
    print(json.dumps(result, indent=4))
    print("\n================================\n")
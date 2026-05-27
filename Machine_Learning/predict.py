# Machine_Learning/predict.py

import json
import joblib
import pandas as pd
import numpy as np

from Machine_Learning.constants import MODEL_PATH, FEATURES_PATH
from Machine_Learning.preprocessing import preprocess_dataframe
from Machine_Learning.feature_engineering import create_features


# =========================================================
# BILL CALCULATION ENGINE
# =========================================================
def calculate_electricity_bill(units: float):
    units = max(units, 0)

    if units <= 100:
        return units * 5
    elif units <= 300:
        return (100 * 5) + (units - 100) * 7
    else:
        return (100 * 5) + (200 * 7) + (units - 300) * 10


# =========================================================
# LOAD MODEL + FEATURES
# =========================================================
def load_model():
    return joblib.load(MODEL_PATH)


def load_feature_names():
    with open(FEATURES_PATH, "r") as f:
        data = json.load(f)

    if isinstance(data, dict) and "features" in data:
        return data["features"]

    return data


# =========================================================
# CORE PREDICTION
# =========================================================
def predict_consumption(input_data: dict):

    model = load_model()
    feature_names = load_feature_names()

    # -----------------------------------------------------
    # IMPORTANT: DO NOT ADD FAKE DEFAULTS HERE
    # -----------------------------------------------------
    df = pd.DataFrame([input_data])

    # -----------------------------------------------------
    # PIPELINE (MUST MATCH TRAINING EXACTLY)
    # -----------------------------------------------------
    df = preprocess_dataframe(df)
    df = create_features(df)

    # -----------------------------------------------------
    # ALIGN FEATURES (CRITICAL FIX)
    # -----------------------------------------------------
    df = df.reindex(columns=feature_names, fill_value=0)

    # -----------------------------------------------------
    # PREDICTION
    # -----------------------------------------------------
    pred_log = model.predict(df)[0]

    # IMPORTANT: only apply exp if model was trained on log1p
    pred = np.expm1(pred_log)
    pred = max(float(pred), 0)

    # -----------------------------------------------------
    # BILL
    # -----------------------------------------------------
    bill = calculate_electricity_bill(pred)

    # -----------------------------------------------------
    # LEVEL
    # -----------------------------------------------------
    if pred < 200:
        level = "Low"
    elif pred < 500:
        level = "Moderate"
    else:
        level = "High"

    return {
        "predicted_electricity_consumption": round(pred, 2),
        "estimated_bill_amount": round(float(bill), 2),
        "usage_level": level,
    }
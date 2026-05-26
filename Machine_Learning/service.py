# Machine_Learning/service.py

import pandas as pd
import numpy as np

from Machine_Learning.model_loader import load_model_artifacts
from Machine_Learning.preprocessing import preprocess_dataframe
from Machine_Learning.feature_engineering import create_features


# =========================================================
# LOAD ARTIFACTS (MODEL + FEATURES)
# =========================================================
ARTIFACTS = load_model_artifacts()
MODEL = ARTIFACTS["model"]
FEATURES = ARTIFACTS["feature_names"]


# =========================================================
# SLAB BILL CALCULATION
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
# CORE PREDICTION PIPELINE
# =========================================================
def predict(input_data: dict):

    # -----------------------------
    # 1. Convert to DataFrame
    # -----------------------------
    df = pd.DataFrame([input_data])

    # -----------------------------
    # 2. Preprocess
    # -----------------------------
    df = preprocess_dataframe(df)

    # -----------------------------
    # 3. Feature Engineering
    # -----------------------------
    df = create_features(df)

    # -----------------------------
    # 4. One-hot + Align
    # -----------------------------
    df = pd.get_dummies(df)
    df = df.reindex(columns=FEATURES, fill_value=0)

    # -----------------------------
    # 5. Predict
    # -----------------------------
    pred_log = MODEL.predict(df)[0]
    pred = np.expm1(pred_log)

    pred = max(pred, 0)

    # -----------------------------
    # 6. Business Logic
    # -----------------------------
    bill = calculate_electricity_bill(pred)

    if pred < 200:
        level = "Low"
    elif pred < 500:
        level = "Moderate"
    else:
        level = "High"

    # -----------------------------
    return {
        "predicted_electricity_consumption": round(float(pred), 2),
        "estimated_bill_amount": round(float(bill), 2),
        "usage_level": level,
    }
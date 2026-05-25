# Machine_Learning/predict.py

import pandas as pd
import numpy as np
import pickle
import torch

from Machine_Learning.model_loader import load_model


# ----------------------------
# Load artifacts (same as training)
# ----------------------------
SCALER_PATH = "Machine_Learning/model_versions/scaler.pkl"
FEATURES_PATH = "Machine_Learning/model_versions/features.json"
USER_MAPPING_PATH = "Machine_Learning/model_versions/user_id_mapping.pkl"


def load_artifacts():
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)

    with open(FEATURES_PATH, "r") as f:
        feature_names = __import__("json").load(f)

    with open(USER_MAPPING_PATH, "rb") as f:
        user_mapping = pickle.load(f)

    return scaler, feature_names, user_mapping


# ----------------------------
# Feature builder (must match training)
# ----------------------------
def build_features(df: pd.DataFrame):
    # basic feature engineering (same logic as Methods.py intent)
    df["people_per_room"] = df["one"] / (df["three"] + 1)

    df["vacation_factor"] = df["eighteen"] * 0.1

    df["appliance_score"] = (
        df["four"] + df["five"] + df["six"] + df["seven"] +
        df["eight"] + df["nine"] + df["ten"] + df["eleven"] +
        df["twelve"] + df["thirteen"]
    )

    df["luxury_score"] = df["fifteen"] + df["sixteen"]

    return df


# ----------------------------
# Main prediction function
# ----------------------------
def predict_consumption(input_data: dict):

    model = load_model()
    scaler, feature_names, user_mapping = load_artifacts()

    df = pd.DataFrame([input_data])

    # ----------------------------
    # Convert booleans → int
    # ----------------------------
    bool_cols = [
        "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen",
        "fifteen", "sixteen"
    ]

    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(int)

    # ----------------------------
    # Convert climate
    # ----------------------------
    climate_map = {
        "hot": 2,
        "moderate": 1,
        "cold": 0
    }

    if "nineteen" in df.columns:
        df["nineteen"] = df["nineteen"].map(climate_map).fillna(1)

    # ----------------------------
    # Feature engineering
    # ----------------------------
    df = build_features(df)

    # ----------------------------
    # Encode month/climate if missing in input
    # (safe fallback)
    # ----------------------------
    if "month" not in df.columns:
        df["month"] = 1

    if "seventeen" not in df.columns:
        df["seventeen"] = 1

    # ----------------------------
    # One-hot encoding (same as training)
    # ----------------------------
    df = pd.get_dummies(
        df,
        columns=["month", "nineteen", "seventeen"],
        prefix=["month", "climate", "vacation_month"],
        drop_first=False
    )

    # ----------------------------
    # Align features EXACTLY with training
    # ----------------------------
    df = df.reindex(columns=feature_names, fill_value=0)

    # ----------------------------
    # Scale features
    # ----------------------------
    X_scaled = scaler.transform(df)

    X_tensor = torch.tensor(X_scaled, dtype=torch.float32)

    # ----------------------------
    # Predict
    # ----------------------------
    model.eval()
    with torch.no_grad():
        prediction = model(X_tensor).numpy()[0][0]

    # reverse log1p if training used it
    prediction = np.expm1(prediction)

    return {
        "predicted_electricity_consumption": round(float(prediction), 2)
    }


# ----------------------------
# Test run
# ----------------------------
if __name__ == "__main__":

    sample_input = {
        "one": 5,
        "two": 2,
        "three": 3,
        "four": True,
        "five": True,
        "six": True,
        "seven": True,
        "eight": False,
        "nine": True,
        "ten": True,
        "eleven": True,
        "twelve": False,
        "thirteen": False,
        "fourteen": 1400,
        "fifteen": False,
        "sixteen": True,
        "eighteen": 10,
        "nineteen": "hot",
        "month": 6,
        "seventeen": 1
    }

    result = predict_consumption(sample_input)
    print(result)
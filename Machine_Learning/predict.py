# Machine_Learning/predict.py

import pandas as pd
import numpy as np
import torch

from Machine_Learning.Methods import ConsumptionModel
from Machine_Learning.constants import MODEL_PATH

import pickle
import json


# ----------------------------
# LOAD ARTIFACTS
# ----------------------------
SCALER_PATH = "Machine_Learning/model_versions/scaler.pkl"
FEATURES_PATH = "Machine_Learning/model_versions/features.json"


def load_artifacts():
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)

    with open(FEATURES_PATH, "r") as f:
        feature_names = json.load(f)

    return scaler, feature_names


# ----------------------------
# FEATURE ENGINEERING (must match training)
# ----------------------------
def build_features(df: pd.DataFrame):

    df["people_per_room"] = df["one"] / (df["three"].replace(0, 1))
    df["vacation_factor"] = df["eighteen"] * 0.1

    df["appliance_score"] = (
        df.get("four", 0) + df.get("five", 0) + df.get("six", 0) +
        df.get("seven", 0) + df.get("eight", 0) + df.get("nine", 0) +
        df.get("ten", 0) + df.get("eleven", 0) + df.get("twelve", 0) +
        df.get("thirteen", 0)
    )

    df["luxury_score"] = df.get("fifteen", 0) + df.get("sixteen", 0)

    return df


# ----------------------------
# MODEL LOADER (PYTORCH FIXED)
# ----------------------------
def load_model(input_dim, num_users=1):

    model = ConsumptionModel(
        num_users=num_users,
        input_dim=input_dim,
        hidden_dim1=128,
        hidden_dim2=64,
        embedding_dim=32,
        dropout_rate=0.2
    )

    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()

    return model


# ----------------------------
# MAIN PREDICTION FUNCTION
# ----------------------------
def predict_consumption(input_data: dict):

    scaler, feature_names = load_artifacts()

    df = pd.DataFrame([input_data])

    # ----------------------------
    # BOOLEAN CONVERSION
    # ----------------------------
    bool_cols = [
        "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen",
        "fifteen", "sixteen"
    ]

    for col in bool_cols:
        df[col] = df.get(col, 0).astype(int)

    # ----------------------------
    # CLIMATE ENCODING
    # ----------------------------
    climate_map = {"hot": 2, "moderate": 1, "cold": 0}

    df["nineteen"] = df.get("nineteen", "moderate")
    df["nineteen"] = df["nineteen"].map(climate_map).fillna(1)

    # ----------------------------
    # DEFAULTS
    # ----------------------------
    df["month"] = df.get("month", 1)
    df["seventeen"] = df.get("seventeen", 1)

    # ----------------------------
    # FEATURE ENGINEERING
    # ----------------------------
    df = build_features(df)

    # ----------------------------
    # ONE HOT ENCODING
    # ----------------------------
    df = pd.get_dummies(
        df,
        columns=["month", "nineteen", "seventeen"],
        prefix=["month", "climate", "vacation_month"],
        drop_first=False
    )

    # ----------------------------
    # ALIGN FEATURES
    # ----------------------------
    df = df.reindex(columns=feature_names, fill_value=0)

    # ----------------------------
    # SCALE
    # ----------------------------
    X_scaled = scaler.transform(df)
    X_tensor = torch.tensor(X_scaled, dtype=torch.float32)

    # ----------------------------
    # LOAD MODEL (SAFE)
    # ----------------------------
    model = load_model(input_dim=X_tensor.shape[1])

    # ----------------------------
    # PREDICT
    # ----------------------------
    with torch.no_grad():
        prediction = model(X_tensor).cpu().numpy()[0][0]

    # reverse log1p if used in training
    prediction = np.expm1(prediction)

    return {
        "predicted_electricity_consumption": round(float(prediction), 2)
    }


# ----------------------------
# TEST
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
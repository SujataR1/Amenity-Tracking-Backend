# Machine_Learning/model_loader.py

import os
import json
import joblib

from Machine_Learning.constants import (
    MODEL_PATH,
    FEATURES_PATH,
)


# =========================================================
# LOAD TRAINED MODEL
# =========================================================
def load_model():

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found at:\n{MODEL_PATH}"
        )

    model = joblib.load(MODEL_PATH)

    return model


# =========================================================
# LOAD FEATURE NAMES (ROBUST FORMAT HANDLING)
# =========================================================
def load_feature_names():

    if not os.path.exists(FEATURES_PATH):
        raise FileNotFoundError(
            f"Features file not found at:\n{FEATURES_PATH}"
        )

    with open(FEATURES_PATH, "r") as f:
        data = json.load(f)

    # =====================================================
    # HANDLE BOTH OLD + NEW FORMATS SAFELY
    # =====================================================

    # NEW FORMAT: {"features": [...]}
    if isinstance(data, dict) and "features" in data:
        feature_names = data["features"]

    # OLD FORMAT: [...]
    elif isinstance(data, list):
        feature_names = data

    else:
        raise ValueError(
            "Invalid feature file format. Expected dict with 'features' or list."
        )

    # Safety check
    if not feature_names:
        raise ValueError("Feature list is empty.")

    return feature_names


# =========================================================
# LOAD ALL ARTIFACTS
# =========================================================
def load_model_artifacts():

    model = load_model()
    feature_names = load_feature_names()

    return {
        "model": model,
        "feature_names": feature_names,
    }


# =========================================================
# TEST BLOCK
# =========================================================
if __name__ == "__main__":

    artifacts = load_model_artifacts()

    print("\n========== MODEL ARTIFACTS ==========\n")

    print("Model Loaded Successfully:")
    print(type(artifacts["model"]))

    print(f"\nTotal Features: {len(artifacts['feature_names'])}")

    print("\nFirst 10 Features:\n")
    print(artifacts["feature_names"][:10])

    print("\n====================================\n")
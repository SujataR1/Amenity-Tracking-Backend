# Machine_Learning/model_loader.py

import os
import json
import joblib

from Machine_Learning.constants import (
    MODEL_PATH,
    FEATURES_PATH,
)


# =========================================================
# LOAD TRAINED XGBOOST MODEL
# =========================================================
def load_model():

    # -----------------------------------------------------
    # CHECK MODEL EXISTS
    # -----------------------------------------------------
    if not os.path.exists(MODEL_PATH):

        raise FileNotFoundError(
            f"Model file not found at:\n{MODEL_PATH}"
        )

    # -----------------------------------------------------
    # LOAD MODEL
    # -----------------------------------------------------
    model = joblib.load(MODEL_PATH)

    return model


# =========================================================
# LOAD FEATURE NAMES
# =========================================================
def load_feature_names():

    # -----------------------------------------------------
    # CHECK FEATURES FILE EXISTS
    # -----------------------------------------------------
    if not os.path.exists(FEATURES_PATH):

        raise FileNotFoundError(
            f"Features file not found at:\n{FEATURES_PATH}"
        )

    # -----------------------------------------------------
    # LOAD FEATURES
    # -----------------------------------------------------
    with open(FEATURES_PATH, "r") as f:

        feature_names = json.load(f)

    return feature_names


# =========================================================
# LOAD ALL MODEL ARTIFACTS
# =========================================================
def load_model_artifacts():

    model = load_model()

    feature_names = load_feature_names()

    return {
        "model": model,
        "feature_names": feature_names,
    }


# =========================================================
# TEST
# =========================================================
if __name__ == "__main__":

    artifacts = load_model_artifacts()

    print("\n========== MODEL ARTIFACTS ==========\n")

    print(
        "Model Loaded Successfully:"
    )

    print(
        type(artifacts["model"])
    )

    print(
        f"\nTotal Features: "
        f"{len(artifacts['feature_names'])}"
    )

    print("\nFirst 10 Features:\n")

    print(
        artifacts["feature_names"][:10]
    )

    print("\n====================================\n")
# Machine_Learning/predict.py

import json
import joblib
import pandas as pd
import numpy as np

from Machine_Learning.constants import (
    MODEL_PATH,
    FEATURES_PATH,
)

from Machine_Learning.preprocessing import (
    preprocess_dataframe,
)

from Machine_Learning.feature_engineering import (
    create_features,
)


# =========================================================
# BILL CALCULATION ENGINE
# =========================================================
def calculate_electricity_bill(units: float):

    units = max(units, 0)

    # -----------------------------------------------------
    # SAMPLE SLAB LOGIC
    # -----------------------------------------------------
    if units <= 100:

        bill = units * 5

    elif units <= 300:

        bill = (
            (100 * 5)
            +
            ((units - 100) * 7)
        )

    else:

        bill = (
            (100 * 5)
            +
            (200 * 7)
            +
            ((units - 300) * 10)
        )

    return round(float(bill), 2)


# =========================================================
# LOAD MODEL
# =========================================================
def load_model():

    model = joblib.load(MODEL_PATH)

    return model


# =========================================================
# LOAD FEATURE NAMES
# =========================================================
def load_feature_names():

    with open(FEATURES_PATH, "r") as f:

        feature_names = json.load(f)

    return feature_names


# =========================================================
# PREPARE INPUT DATAFRAME
# =========================================================
def prepare_input_dataframe(
    input_data: dict,
) -> pd.DataFrame:

    df = pd.DataFrame([input_data])

    # -----------------------------------------------------
    # REQUIRED DEFAULTS
    # -----------------------------------------------------
    defaults = {
        "one": 0,
        "two": 0,
        "three": 1,
        "four": 0,
        "five": 0,
        "six": 0,
        "seven": 0,
        "eight": 0,
        "nine": 0,
        "ten": 0,
        "eleven": 0,
        "twelve": 0,
        "thirteen": 0,
        "fourteen": 0,
        "fifteen": 0,
        "sixteen": 0,
        "seventeen": "january",
        "eighteen": 0,
        "nineteen": "moderate",
        "month": 1,
        "year": 2025,
    }

    # -----------------------------------------------------
    # ENSURE ALL COLUMNS EXIST
    # -----------------------------------------------------
    for col, default_value in defaults.items():

        if col not in df.columns:

            df[col] = default_value

    return df


# =========================================================
# ALIGN FEATURES
# =========================================================
def align_features(
    df: pd.DataFrame,
    feature_names: list,
) -> pd.DataFrame:

    # -----------------------------------------------------
    # ONE HOT ENCODING
    # -----------------------------------------------------
    categorical_columns = []

    if "seventeen" in df.columns:
        categorical_columns.append("seventeen")

    if categorical_columns:

        df = pd.get_dummies(
            df,
            columns=categorical_columns,
            drop_first=False,
        )

    # -----------------------------------------------------
    # ALIGN TO TRAINING FEATURES
    # -----------------------------------------------------
    df = df.reindex(
        columns=feature_names,
        fill_value=0,
    )

    return df


# =========================================================
# MAIN PREDICTION FUNCTION
# =========================================================
def predict_consumption(
    input_data: dict,
):

    # -----------------------------------------------------
    # LOAD MODEL + FEATURES
    # -----------------------------------------------------
    model = load_model()

    feature_names = load_feature_names()

    # -----------------------------------------------------
    # CREATE DATAFRAME
    # -----------------------------------------------------
    df = prepare_input_dataframe(
        input_data,
    )

    # -----------------------------------------------------
    # PREPROCESSING
    # -----------------------------------------------------
    df = preprocess_dataframe(df)

    # -----------------------------------------------------
    # FEATURE ENGINEERING
    # -----------------------------------------------------
    df = create_features(df)

    # -----------------------------------------------------
    # FEATURE ALIGNMENT
    # -----------------------------------------------------
    df = align_features(
        df,
        feature_names,
    )

    # -----------------------------------------------------
    # PREDICTION
    # -----------------------------------------------------
    prediction = model.predict(df)[0]

    # -----------------------------------------------------
    # REVERSE LOG TRANSFORM
    # -----------------------------------------------------
    prediction = np.expm1(prediction)

    # -----------------------------------------------------
    # SAFETY
    # -----------------------------------------------------
    prediction = max(prediction, 0)

    # -----------------------------------------------------
    # BILL ESTIMATION
    # -----------------------------------------------------
    estimated_bill = calculate_electricity_bill(
        prediction,
    )

    # -----------------------------------------------------
    # CONSUMPTION LEVEL
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
        "predicted_electricity_consumption": round(
            float(prediction),
            2,
        ),

        "estimated_bill_amount": round(
            float(estimated_bill),
            2,
        ),

        "usage_level": usage_level,
    }


# =========================================================
# TESTING
# =========================================================
if __name__ == "__main__":

    sample_input = {

        # -------------------------------------------------
        # QUESTIONNAIRE DATA
        # -------------------------------------------------
        "one": 5,
        "two": 2,
        "three": 3,

        # -------------------------------------------------
        # APPLIANCES
        # -------------------------------------------------
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

        # -------------------------------------------------
        # HOME DETAILS
        # -------------------------------------------------
        "fourteen": 1400,

        "fifteen": False,
        "sixteen": True,

        # -------------------------------------------------
        # VACATION
        # -------------------------------------------------
        "seventeen": "june",

        "eighteen": 10,

        # -------------------------------------------------
        # CLIMATE
        # -------------------------------------------------
        "nineteen": "hot",

        # -------------------------------------------------
        # TIME
        # -------------------------------------------------
        "month": 6,
        "year": 2025,

        # -------------------------------------------------
        # OPTIONAL HISTORICAL FEATURES
        # -------------------------------------------------
        "last_month_consumption": 420,

        "avg_last_3_months": 410,

        "avg_last_6_months": 395,

        "consumption_growth_rate": 0.08,
    }

    result = predict_consumption(
        sample_input,
    )

    print("\n========== PREDICTION ==========")

    print(json.dumps(result, indent=4))

    print("================================\n")
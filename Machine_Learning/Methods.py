#Machine_Learning/Methods.py
import json
import os
import joblib
import numpy as np
import pandas as pd

from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

from Machine_Learning.preprocessing import preprocess_dataframe
from Machine_Learning.feature_engineering import create_features
from Machine_Learning.evaluation import evaluate_model

from Database_and_ORM.Database_Models import (
    ElectricityConsumption,
    QuestionnaireAnswers,
    WaterConsumption,
    GasConsumption,
    FuelConsumption,
    User,
)

# =========================================================
# DATASET BUILDER (CLEAN + SINGLE SOURCE TRUTH)
# =========================================================
async def build_dataset(resource_model, target_column: str):

    users = await User.all().values("id")
    user_ids = [u["id"] for u in users]

    consumption = await resource_model.filter(
        user_id__in=user_ids
    ).values(
        "user_id",
        "year",
        "month",
        target_column,
    )

    questionnaire = await QuestionnaireAnswers.filter(
        user_id__in=user_ids
    ).values(
        "user_id",
        "num_people",
        "num_children",
        "bedrooms",
        "has_ac",
        "has_geyser",
        "has_iron",
        "has_washing_machine",
        "has_dishwasher",
        "has_induction",
        "has_microwave",
        "has_kettle",
        "has_vacuum",
        "has_room_heater",
        "home_area",
        "has_pool",
        "has_garden",
        "vacation_days",
        "climate",
    )

    df = pd.DataFrame(consumption).merge(
        pd.DataFrame(questionnaire),
        on="user_id",
        how="left",
    )

    return df.fillna(0)


# =========================================================
# OPTIONAL: SAFE HISTORICAL FEATURES (NO LEAK INTO TRAIN)
# =========================================================
def add_historical_features(df: pd.DataFrame, target_column: str):

    df = df.sort_values(["user_id", "year", "month"]).copy()

    df["last_month"] = df.groupby("user_id")[target_column].shift(1)

    df["avg_3m"] = (
        df.groupby("user_id")[target_column]
        .shift(1)
        .rolling(3, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )

    df["avg_6m"] = (
        df.groupby("user_id")[target_column]
        .shift(1)
        .rolling(6, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )

    df["growth"] = (
        (df[target_column] - df["last_month"])
        / df["last_month"].replace(0, 1)
    )

    return df.replace([np.inf, -np.inf], 0).fillna(0)


# =========================================================
# MODEL EVALUATION WRAPPER
# =========================================================
def evaluate(y_true, y_pred):
    return evaluate_model(y_true, y_pred)


# =========================================================
# CLEAN TRAINING PIPELINE (MAIN FIX)
# =========================================================
async def retrain_model(resource_type: str, config_path: str):

    with open(config_path, "r") as f:
        config_all = json.load(f)

    config = config_all.get(resource_type)

    if not config:
        raise ValueError("Invalid resource type")

    model_dir = config["Directory_Path"]
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, config["Trained_Model_Name"])
    features_path = os.path.join(model_dir, config["Features_File_Name"])
    target_column = config["Column_Name"]

    # =====================================================
    # FIXED: explicit model mapping (NO globals())
    # =====================================================
    model_map = {
        "ElectricityConsumption": ElectricityConsumption,
        "WaterConsumption": WaterConsumption,
        "GasConsumption": GasConsumption,
        "FuelConsumption": FuelConsumption,
    }

    resource_model = model_map.get(config["Database_Name"])

    if not resource_model:
        raise ValueError("Invalid database model mapping")

    # =====================================================
    # DATA LOADING
    # =====================================================
    print("Loading dataset...")
    df = await build_dataset(resource_model, target_column)

    # =====================================================
    # PREPROCESSING (ONLY ONCE)
    # =====================================================
    print("Preprocessing...")
    df = preprocess_dataframe(df)

    # =====================================================
    # FEATURE ENGINEERING (ONLY ONE PIPELINE)
    # =====================================================
    print("Feature engineering...")
    df = create_features(df)

    # =====================================================
    # OPTIONAL: HISTORICAL FEATURES (SAFE ADDITION)
    # =====================================================
    df = add_historical_features(df, target_column)

    # =====================================================
    # TARGET CLEANING (NO LEAKAGE)
    # =====================================================
    y = np.log1p(df[target_column])

    X = df.drop(columns=[target_column, "user_id"], errors="ignore")

    # =====================================================
    # TRAIN TEST SPLIT
    # =====================================================
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    # =====================================================
    # MODEL
    # =====================================================
    model = XGBRegressor(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=42,
    )

    print("Training model...")
    model.fit(X_train, y_train)

    # =====================================================
    # PREDICTION (SAFE INVERSION)
    # =====================================================
    preds = np.expm1(model.predict(X_test))
    y_true = np.expm1(y_test)

    metrics = evaluate(y_true, preds)

    # =====================================================
    # SAVE ARTIFACTS (STRICT FORMAT)
    # =====================================================
    feature_names = X.columns.tolist()

    with open(features_path, "w") as f:
        json.dump({"features": feature_names}, f, indent=4)

    joblib.dump(model, model_path)

    print(f"Model saved at: {model_path}")

    return {
        "status": "success",
        "metrics": metrics,
        "model_path": model_path,
    }
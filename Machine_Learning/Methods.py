# Machine_Learning/Methods.py

import json
import pickle
import pandas as pd
import numpy as np
import os
import joblib

from xgboost import XGBRegressor

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from Database_and_ORM.Database_Models import (
    ElectricityConsumption,
    QuestionnaireAnswers,
    User,
)

from Machine_Learning.preprocessing import preprocess_dataframe
from Machine_Learning.feature_engineering import create_features


# =========================================================
# DATASET BUILDER
# =========================================================
async def build_dataset(resource_model, target_column):

    users = await User.all().values("id")

    user_ids = [u["id"] for u in users]

    # -----------------------------------------------------
    # CONSUMPTION DATA
    # -----------------------------------------------------
    consumption = await resource_model.filter(
        user_id__in=user_ids
    ).values(
        "user_id",
        "year",
        "month",
        target_column,
    )

    # -----------------------------------------------------
    # QUESTIONNAIRE DATA
    # -----------------------------------------------------
    questionnaire = await QuestionnaireAnswers.filter(
        user_id__in=user_ids
    ).values(
        "user_id",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
    )

    # -----------------------------------------------------
    # DATAFRAMES
    # -----------------------------------------------------
    df_consumption = pd.DataFrame(consumption)

    df_questionnaire = pd.DataFrame(questionnaire)

    # -----------------------------------------------------
    # MERGE
    # -----------------------------------------------------
    df = df_consumption.merge(
        df_questionnaire,
        on="user_id",
        how="left",
    )

    # -----------------------------------------------------
    # CLEANUP
    # -----------------------------------------------------
    df.fillna(0, inplace=True)

    return df


# =========================================================
# HISTORICAL FEATURE ENGINEERING
# =========================================================
def add_historical_features(
    df: pd.DataFrame,
    target_column: str,
) -> pd.DataFrame:

    df = df.copy()

    # -----------------------------------------------------
    # SORT FOR TIME SERIES
    # -----------------------------------------------------
    df = df.sort_values(
        by=["user_id", "year", "month"]
    )

    # -----------------------------------------------------
    # LAST MONTH CONSUMPTION
    # -----------------------------------------------------
    df["last_month_consumption"] = (
        df.groupby("user_id")[target_column]
        .shift(1)
    )

    # -----------------------------------------------------
    # LAST 3 MONTH AVERAGE
    # -----------------------------------------------------
    df["avg_last_3_months"] = (
        df.groupby("user_id")[target_column]
        .transform(
            lambda x: x.shift(1).rolling(3, min_periods=1).mean()
        )
    )

    # -----------------------------------------------------
    # LAST 6 MONTH AVERAGE
    # -----------------------------------------------------
    df["avg_last_6_months"] = (
        df.groupby("user_id")[target_column]
        .transform(
            lambda x: x.shift(1).rolling(6, min_periods=1).mean()
        )
    )

    # -----------------------------------------------------
    # GROWTH RATE
    # -----------------------------------------------------
    df["consumption_growth_rate"] = (
        (
            df[target_column]
            - df["last_month_consumption"]
        )
        /
        (
            df["last_month_consumption"].replace(0, 1)
        )
    )

    # -----------------------------------------------------
    # YEARLY USER AVERAGE
    # -----------------------------------------------------
    df["yearly_avg_consumption"] = (
        df.groupby("user_id")[target_column]
        .transform("mean")
    )

    # -----------------------------------------------------
    # CLEANUP
    # -----------------------------------------------------
    df.replace([np.inf, -np.inf], 0, inplace=True)

    df.fillna(0, inplace=True)

    return df


# =========================================================
# MODEL EVALUATION
# =========================================================
def evaluate_model(y_true, y_pred):

    mae = mean_absolute_error(y_true, y_pred)

    mse = mean_squared_error(y_true, y_pred)

    rmse = np.sqrt(mse)

    r2 = r2_score(y_true, y_pred)

    print("\n========== MODEL EVALUATION ==========")

    print(f"MAE  : {mae}")

    print(f"MSE  : {mse}")

    print(f"RMSE : {rmse}")

    print(f"R2   : {r2}")

    print("======================================\n")

    return {
        "mae": float(mae),
        "mse": float(mse),
        "rmse": float(rmse),
        "r2": float(r2),
    }


# =========================================================
# TRAINING PIPELINE
# =========================================================
async def retrain_model(resource_type: str):

    # -----------------------------------------------------
    # LOAD CONFIG
    # -----------------------------------------------------
    with open(
        "Machine_Learning/Machine_Learning_Parameter_Schemas.json",
        "r",
    ) as f:

        config_all = json.load(f)

    config = config_all.get(resource_type)

    if not config:
        raise ValueError("Invalid resource type config")

    # -----------------------------------------------------
    # PATHS
    # -----------------------------------------------------
    model_dir = config["Directory_Path"]

    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(
        model_dir,
        config["Trained_Model_Name"],
    )

    features_path = os.path.join(
        model_dir,
        config["Features_File_Name"],
    )

    target_column = config["Column_Name"]

    resource_model = globals()[config["Database_Name"]]

    # -----------------------------------------------------
    # LOAD DATA
    # -----------------------------------------------------
    print("Loading dataset...")

    df = await build_dataset(
        resource_model,
        target_column,
    )

    # -----------------------------------------------------
    # PREPROCESSING
    # -----------------------------------------------------
    print("Preprocessing dataset...")

    df = preprocess_dataframe(df)

    # -----------------------------------------------------
    # FEATURE ENGINEERING
    # -----------------------------------------------------
    print("Creating features...")

    df = create_features(df)

    # -----------------------------------------------------
    # HISTORICAL FEATURES
    # -----------------------------------------------------
    print("Creating historical features...")

    df = add_historical_features(
        df,
        target_column,
    )

    # -----------------------------------------------------
    # TARGET CLEANING
    # -----------------------------------------------------
    df[target_column] = np.clip(
        df[target_column],
        df[target_column].quantile(0.01),
        df[target_column].quantile(0.99),
    )

    # -----------------------------------------------------
    # CYCLICAL MONTH FEATURES
    # -----------------------------------------------------
    df["month_sin"] = np.sin(
        2 * np.pi * df["month"] / 12
    )

    df["month_cos"] = np.cos(
        2 * np.pi * df["month"] / 12
    )

    # -----------------------------------------------------
    # ONE HOT ENCODING
    # -----------------------------------------------------
    categorical_columns = [
        "nineteen",
        "seventeen",
    ]

    df = pd.get_dummies(
        df,
        columns=categorical_columns,
        drop_first=False,
    )

    # -----------------------------------------------------
    # DROP UNUSED COLUMNS
    # -----------------------------------------------------
    drop_columns = [
        target_column,
    ]

    if "user_id" in df.columns:
        drop_columns.append("user_id")

    # -----------------------------------------------------
    # FEATURES / TARGET
    # -----------------------------------------------------
    X = df.drop(columns=drop_columns)

    y = np.log1p(df[target_column])

    # -----------------------------------------------------
    # STORE FEATURE NAMES
    # -----------------------------------------------------
    feature_names = X.columns.tolist()

    with open(features_path, "w") as f:
        json.dump(feature_names, f)

    # -----------------------------------------------------
    # TRAIN TEST SPLIT
    # -----------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    # =====================================================
    # XGBOOST MODEL
    # =====================================================
    print("Training XGBoost model...")

    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=6,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=42,
    )

    # -----------------------------------------------------
    # TRAIN
    # -----------------------------------------------------
    model.fit(
        X_train,
        y_train,
    )

    # -----------------------------------------------------
    # PREDICT
    # -----------------------------------------------------
    predictions = model.predict(X_test)

    predictions = np.expm1(predictions)

    y_test_actual = np.expm1(y_test)

    # -----------------------------------------------------
    # EVALUATION
    # -----------------------------------------------------
    metrics = evaluate_model(
        y_test_actual,
        predictions,
    )

    # -----------------------------------------------------
    # SAVE MODEL
    # -----------------------------------------------------
    print("Saving model artifacts...")

    joblib.dump(
        model,
        model_path,
    )

    print(
        f"\n✅ XGBoost model saved successfully at: {model_path}"
    )

    return {
        "status": "success",
        "metrics": metrics,
        "model_path": model_path,
    }
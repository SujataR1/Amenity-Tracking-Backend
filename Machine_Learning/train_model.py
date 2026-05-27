# Machine_Learning/train_model.py

import os
import json
import joblib
import numpy as np
import pandas as pd

from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, cross_val_score

from Machine_Learning.preprocessing import preprocess_dataframe
from Machine_Learning.feature_engineering import create_features
from Machine_Learning.evaluation import evaluate_model
from Machine_Learning.constants import (
    TARGET_COLUMN,
    TEST_SIZE,
    RANDOM_STATE,
    MODEL_PATH,
    FEATURES_PATH,
)

DATASET_PATH = "Machine_Learning/datasets/electricity_sample_data_500_rows.csv"


# =========================================================
# LOAD DATASET
# =========================================================
def load_dataset():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    print("Dataset shape:", df.shape)
    return df


# =========================================================
# OUTLIER HANDLING (ONLY TARGET)
# =========================================================
def remove_outliers(df):
    df = df.copy()

    lower = df[TARGET_COLUMN].quantile(0.01)
    upper = df[TARGET_COLUMN].quantile(0.99)

    df[TARGET_COLUMN] = np.clip(df[TARGET_COLUMN], lower, upper)
    return df


# =========================================================
# PIPELINE (FIXED - NO DATA LEAKAGE)
# =========================================================
def prepare_data(df):

    # -----------------------------------------------------
    # STEP 1: SPLIT RAW DATA FIRST (IMPORTANT FIX)
    # -----------------------------------------------------
    train_df, test_df = train_test_split(
        df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    # -----------------------------------------------------
    # STEP 2: PREPROCESS SEPARATELY
    # -----------------------------------------------------
    train_df = preprocess_dataframe(train_df)
    test_df = preprocess_dataframe(test_df)

    # -----------------------------------------------------
    # STEP 3: FEATURE ENGINEERING SEPARATELY
    # -----------------------------------------------------
    train_df = create_features(train_df)
    test_df = create_features(test_df)

    # -----------------------------------------------------
    # STEP 4: OUTLIER HANDLING (TRAIN ONLY EFFECT)
    # -----------------------------------------------------
    train_df = remove_outliers(train_df)
    test_df = remove_outliers(test_df)

    # -----------------------------------------------------
    # STEP 5: SPLIT X / Y
    # -----------------------------------------------------
    y_train = np.log1p(train_df[TARGET_COLUMN])
    y_test = np.log1p(test_df[TARGET_COLUMN])

    X_train = train_df.drop(columns=[TARGET_COLUMN])
    X_test = test_df.drop(columns=[TARGET_COLUMN])

    # -----------------------------------------------------
    # STEP 6: ONE HOT ENCODING
    # -----------------------------------------------------
    X_train = pd.get_dummies(X_train)
    X_test = pd.get_dummies(X_test)

    # -----------------------------------------------------
    # STEP 7: ALIGN COLUMNS (CRITICAL FIX)
    # -----------------------------------------------------
    X_train, X_test = X_train.align(
        X_test,
        join="left",
        axis=1,
        fill_value=0
    )

    # -----------------------------------------------------
    # STEP 8: SAVE FEATURE LIST
    # -----------------------------------------------------
    os.makedirs(os.path.dirname(FEATURES_PATH), exist_ok=True)

    feature_list = X_train.columns.tolist()

    with open(FEATURES_PATH, "w") as f:
        json.dump({"features": feature_list}, f, indent=4)

    return X_train, X_test, y_train, y_test


# =========================================================
# MODEL
# =========================================================
def build_model():
    return XGBRegressor(
        objective="reg:squarederror",
        n_estimators=600,
        learning_rate=0.03,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.5,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )


# =========================================================
# TRAIN
# =========================================================
def train_model():

    df = load_dataset()
    X_train, X_test, y_train, y_test = prepare_data(df)

    model = build_model()

    print("\nTraining model...")
    model.fit(X_train, y_train)

    # --------------------------
    # PREDICTION
    # --------------------------
    preds = model.predict(X_test)

    preds_actual = np.expm1(preds)
    y_test_actual = np.expm1(y_test)

    metrics = evaluate_model(y_test_actual, preds_actual)

    # --------------------------
    # SCORES
    # --------------------------
    train_r2 = model.score(X_train, y_train)
    test_r2 = model.score(X_test, y_test)

    print("\n========== PERFORMANCE ==========")
    print("Train R2:", train_r2)
    print("Test R2 :", test_r2)

    # --------------------------
    # CROSS VALIDATION
    # --------------------------
    cv_scores = cross_val_score(
        model,
        X_train,
        y_train,
        cv=5,
        scoring="r2",
        n_jobs=-1,
    )

    print("CV mean:", cv_scores.mean())

    # --------------------------
    # SAVE MODEL
    # --------------------------
    joblib.dump(model, MODEL_PATH)

    print("\nModel saved at:", MODEL_PATH)

    return {
        "metrics": metrics,
        "train_r2": float(train_r2),
        "test_r2": float(test_r2),
        "cv_score": float(cv_scores.mean()),
    }


if __name__ == "__main__":
    result = train_model()
    print(json.dumps(result, indent=4))
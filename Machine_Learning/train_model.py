# Machine_Learning/train_model.py

import os
import json
import joblib
import numpy as np
import pandas as pd
import sys

from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, cross_val_score

# =========================================================
# FIX: PATH SETUP (MUST BE FIRST)
# =========================================================
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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

# =========================================================
# CONFIG
# =========================================================
DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "datasets",
    "electricity_sample_data_500_rows.csv"
)

np.random.seed(RANDOM_STATE)


# =========================================================
# LOAD DATASET
# =========================================================
def load_dataset():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)

    # safety check
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in dataset")

    print(f"Dataset loaded: {df.shape}")
    return df


# =========================================================
# OUTLIER HANDLING (TRAIN ONLY)
# =========================================================
def remove_outliers_train_only(df: pd.DataFrame):
    df = df.copy()

    lower = df[TARGET_COLUMN].quantile(0.01)
    upper = df[TARGET_COLUMN].quantile(0.99)

    df = df[(df[TARGET_COLUMN] >= lower) & (df[TARGET_COLUMN] <= upper)]

    return df


# =========================================================
# FEATURE PIPELINE
# =========================================================
def build_features(df: pd.DataFrame):
    df = preprocess_dataframe(df)
    df = create_features(df)
    return df


# =========================================================
# DATA PREP
# =========================================================
def prepare_data(df):

    # ----------------------------
    # SPLIT FIRST (IMPORTANT)
    # ----------------------------
    train_df, test_df = train_test_split(
        df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    # ----------------------------
    # OUTLIER REMOVAL (TRAIN ONLY)
    # ----------------------------
    train_df = remove_outliers_train_only(train_df)

    # ----------------------------
    # FEATURE ENGINEERING
    # ----------------------------
    train_df = build_features(train_df)
    test_df = build_features(test_df)

    # ----------------------------
    # TARGET SPLIT
    # ----------------------------
    y_train = np.log1p(train_df[TARGET_COLUMN])
    y_test = np.log1p(test_df[TARGET_COLUMN])

    X_train = train_df.drop(columns=[TARGET_COLUMN])
    X_test = test_df.drop(columns=[TARGET_COLUMN])

    # ----------------------------
    # ENCODING
    # ----------------------------
    X_train = pd.get_dummies(X_train)
    X_test = pd.get_dummies(X_test)

    # align columns
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

    # ----------------------------
    # SAVE FEATURE LIST
    # ----------------------------
    os.makedirs(os.path.dirname(FEATURES_PATH), exist_ok=True)

    with open(FEATURES_PATH, "w") as f:
        json.dump({"features": list(X_train.columns)}, f, indent=4)

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
    preds = np.expm1(model.predict(X_test))
    y_true = np.expm1(y_test)

    metrics = evaluate_model(y_true, preds)

    # --------------------------
    # SCORES
    # --------------------------
    train_r2 = model.score(X_train, y_train)
    test_r2 = model.score(X_test, y_test)

    print("\n========== PERFORMANCE ==========")
    print(f"Train R2: {train_r2:.4f}")
    print(f"Test R2 : {test_r2:.4f}")

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

    print(f"CV Mean: {cv_scores.mean():.4f}")

    # --------------------------
    # SAVE MODEL
    # --------------------------
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"\nModel saved at: {MODEL_PATH}")

    return {
        "metrics": metrics,
        "train_r2": float(train_r2),
        "test_r2": float(test_r2),
        "cv_score": float(cv_scores.mean()),
    }


# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    result = train_model()
    print(json.dumps(result, indent=4))
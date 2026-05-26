# Machine_Learning/train_model.py
import os
import json
import joblib
import numpy as np
import pandas as pd

from xgboost import XGBRegressor

from sklearn.model_selection import (
    train_test_split,
    cross_val_score,
)

from Machine_Learning.preprocessing import preprocess_dataframe
from Machine_Learning.feature_engineering import create_features
from Machine_Learning.evaluation import evaluate_model
from Machine_Learning.constants import (
    TARGET_COLUMN,
    TEST_SIZE,
    RANDOM_STATE,
    MODEL_DIRECTORY,
    MODEL_PATH,
    FEATURES_PATH,
)


# =========================================================
# DATASET PATH
# =========================================================
DATASET_PATH = (
    "Machine_Learning/datasets/"
    "electricity_sample_data_500_rows.csv"
)


# =========================================================
# LOAD DATASET
# =========================================================
def load_dataset():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at: {DATASET_PATH}")

    print("\nLoading dataset...")
    df = pd.read_csv(DATASET_PATH)
    print(f"Dataset Shape: {df.shape}")

    return df


# =========================================================
# OUTLIER REMOVAL (SAFE VERSION)
# =========================================================
def remove_outliers_train_only(df, target_column):
    df = df.copy()

    lower = df[target_column].quantile(0.01)
    upper = df[target_column].quantile(0.99)

    df[target_column] = np.clip(df[target_column], lower, upper)

    return df


# =========================================================
# FEATURE PIPELINE (LEAKAGE SAFE ORDER)
# =========================================================
def prepare_data(df):

    print("\nRunning preprocessing pipeline...")
    df = preprocess_dataframe(df)

    # -----------------------------------------------------
    # SPLIT FIRST (IMPORTANT FIX)
    # -----------------------------------------------------
    print("\nSplitting BEFORE feature engineering (FIX)...")

    train_df, test_df = train_test_split(
        df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    # -----------------------------------------------------
    # FEATURE ENGINEERING (TRAIN)
    # -----------------------------------------------------
    print("\nFeature engineering (train)...")
    train_df = create_features(train_df)

    print("\nFeature engineering (test)...")
    test_df = create_features(test_df)

    # -----------------------------------------------------
    # OUTLIERS ONLY ON TRAIN
    # -----------------------------------------------------
    train_df = remove_outliers_train_only(train_df, TARGET_COLUMN)
    test_df = remove_outliers_train_only(test_df, TARGET_COLUMN)

    # -----------------------------------------------------
    # LOG TRANSFORM TARGET
    # -----------------------------------------------------
    print("\nApplying log transform...")

    y_train = np.log1p(train_df[TARGET_COLUMN])
    y_test = np.log1p(test_df[TARGET_COLUMN])

    X_train = train_df.drop(columns=[TARGET_COLUMN])
    X_test = test_df.drop(columns=[TARGET_COLUMN])

    # -----------------------------------------------------
    # ONE HOT ENCODING (CONSISTENT FIX)
    # -----------------------------------------------------
    X_train = pd.get_dummies(X_train)
    X_test = pd.get_dummies(X_test)

    # align columns (VERY IMPORTANT FIX)
    X_train, X_test = X_train.align(X_test, join="left", axis=1, fill_value=0)

    # -----------------------------------------------------
    # CLEANUP
    # -----------------------------------------------------
    X_train.replace([np.inf, -np.inf], 0, inplace=True)
    X_test.replace([np.inf, -np.inf], 0, inplace=True)

    X_train.fillna(0, inplace=True)
    X_test.fillna(0, inplace=True)

    # -----------------------------------------------------
    # SAVE FEATURES
    # -----------------------------------------------------
    os.makedirs(MODEL_DIRECTORY, exist_ok=True)

    with open(FEATURES_PATH, "w") as f:
        json.dump(X_train.columns.tolist(), f)

    print("\nFeature names saved.")

    return X_train, X_test, y_train, y_test


# =========================================================
# MODEL
# =========================================================
def build_model():
    print("\nBuilding XGBoost model...")

    return XGBRegressor(
        objective="reg:squarederror",

        # -------------------------------------------------
        # FIX: reduce overfitting
        # -------------------------------------------------
        n_estimators=300,
        learning_rate=0.05,

        max_depth=4,
        min_child_weight=5,

        subsample=0.8,
        colsample_bytree=0.8,

        # -------------------------------------------------
        # REGULARIZATION (IMPORTANT)
        # -------------------------------------------------
        reg_alpha=0.1,
        reg_lambda=2.0,

        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

# =========================================================
# TRAIN MODEL
# =========================================================
def train_model():

    df = load_dataset()

    X_train, X_test, y_train, y_test = prepare_data(df)

    model = build_model()

    print("\nTraining model...")
    model.fit(X_train, y_train)

    print("\nTraining completed.")

    # -----------------------------------------------------
    # PREDICTIONS
    # -----------------------------------------------------
    preds = model.predict(X_test)

    preds_actual = np.expm1(preds)
    y_test_actual = np.expm1(y_test)

    # -----------------------------------------------------
    # EVALUATION
    # -----------------------------------------------------
    metrics = evaluate_model(y_test_actual, preds_actual)

    # -----------------------------------------------------
    # REAL SCORES (NOT FAKE ACCURACY)
    # -----------------------------------------------------
    train_r2 = model.score(X_train, y_train)
    test_r2 = model.score(X_test, y_test)

    print("\n========== MODEL PERFORMANCE ==========\n")
    print(f"Train R2 : {train_r2:.4f}")
    print(f"Test R2  : {test_r2:.4f}")
    print("\n=======================================\n")

    # -----------------------------------------------------
    # CROSS VALIDATION (SAFE VERSION)
    # -----------------------------------------------------
    print("\nRunning Cross Validation...\n")

    cv_scores = cross_val_score(
        model,
        X_train,
        y_train,
        cv=5,
        scoring="r2",
        n_jobs=-1,
    )

    print("CV Scores:", cv_scores)
    print("Average CV:", cv_scores.mean())

    # -----------------------------------------------------
    # SAVE MODEL
    # -----------------------------------------------------
    print("\nSaving model...")

    joblib.dump(model, MODEL_PATH)

    print(f"\nModel saved at: {MODEL_PATH}")

    # -----------------------------------------------------
    # FEATURE IMPORTANCE
    # -----------------------------------------------------
    importance = pd.DataFrame({
        "feature": X_train.columns,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)

    print("\nTop Features:\n")
    print(importance.head(20))

    return {
        "status": "success",
        "metrics": metrics,
        "train_r2": float(train_r2),
        "test_r2": float(test_r2),
        "cv_score": float(cv_scores.mean()),
    }


# =========================================================
# RUNNER
# =========================================================
if __name__ == "__main__":

    result = train_model()

    print("\n========== FINAL RESULT ==========\n")
    print(json.dumps(result, indent=4))
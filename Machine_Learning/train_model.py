# Machine_Learning/train_model.py

import os
import json
import joblib
import pandas as pd
import numpy as np

from xgboost import XGBRegressor

from sklearn.model_selection import train_test_split

from Machine_Learning.preprocessing import (
    preprocess_dataframe,
)

from Machine_Learning.feature_engineering import (
    create_features,
)

from Machine_Learning.evaluation import (
    evaluate_model,
)

from Machine_Learning.constants import (
    TARGET_COLUMN,
    TEST_SIZE,
    RANDOM_STATE,
    MODEL_DIRECTORY,
    MODEL_PATH,
    FEATURES_PATH,
)


# =========================================================
# TRAINING DATASET PATH
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

        raise FileNotFoundError(
            f"Dataset not found at: {DATASET_PATH}"
        )

    print("\nLoading dataset...")

    df = pd.read_csv(DATASET_PATH)

    print(f"Dataset Shape: {df.shape}")

    return df


# =========================================================
# REMOVE OUTLIERS
# =========================================================
def remove_outliers(
    df: pd.DataFrame,
    target_column: str,
):

    print("\nRemoving extreme outliers...")

    lower_limit = df[target_column].quantile(0.01)

    upper_limit = df[target_column].quantile(0.99)

    df[target_column] = np.clip(
        df[target_column],
        lower_limit,
        upper_limit,
    )

    return df


# =========================================================
# CREATE TRAINING DATA
# =========================================================
def prepare_training_data(
    df: pd.DataFrame,
):

    # -----------------------------------------------------
    # PREPROCESSING
    # -----------------------------------------------------
    print("\nRunning preprocessing pipeline...")

    df = preprocess_dataframe(df)

    # -----------------------------------------------------
    # FEATURE ENGINEERING
    # -----------------------------------------------------
    print("\nRunning feature engineering...")

    df = create_features(df)

    # -----------------------------------------------------
    # REMOVE OUTLIERS
    # -----------------------------------------------------
    df = remove_outliers(
        df,
        TARGET_COLUMN,
    )

    # -----------------------------------------------------
    # LOG TRANSFORM TARGET
    # -----------------------------------------------------
    print("\nApplying log transformation...")

    y = np.log1p(df[TARGET_COLUMN])

    # -----------------------------------------------------
    # DROP TARGET COLUMN
    # -----------------------------------------------------
    X = df.drop(columns=[TARGET_COLUMN])

    # -----------------------------------------------------
    # HANDLE CATEGORICAL DATA
    # -----------------------------------------------------
    categorical_columns = []

    if "seventeen" in X.columns:
        categorical_columns.append("seventeen")

    if categorical_columns:

        X = pd.get_dummies(
            X,
            columns=categorical_columns,
            drop_first=False,
        )

    # -----------------------------------------------------
    # STORE FEATURE NAMES
    # -----------------------------------------------------
    feature_names = X.columns.tolist()

    os.makedirs(
        MODEL_DIRECTORY,
        exist_ok=True,
    )

    with open(FEATURES_PATH, "w") as f:

        json.dump(feature_names, f)

    print("\nFeature names saved.")

    return X, y


# =========================================================
# BUILD XGBOOST MODEL
# =========================================================
def build_model():

    print("\nBuilding XGBoost model...")

    model = XGBRegressor(

        # -------------------------------------------------
        # CORE PARAMETERS
        # -------------------------------------------------
        objective="reg:squarederror",

        n_estimators=500,

        learning_rate=0.03,

        max_depth=6,

        min_child_weight=3,

        subsample=0.8,

        colsample_bytree=0.8,

        gamma=0.1,

        reg_alpha=0.1,

        reg_lambda=1.0,

        # -------------------------------------------------
        # PERFORMANCE
        # -------------------------------------------------
        random_state=RANDOM_STATE,

        n_jobs=-1,
    )

    return model


# =========================================================
# TRAIN MODEL
# =========================================================
def train_model():

    # -----------------------------------------------------
    # LOAD DATASET
    # -----------------------------------------------------
    df = load_dataset()

    # -----------------------------------------------------
    # PREPARE TRAINING DATA
    # -----------------------------------------------------
    X, y = prepare_training_data(df)

    # -----------------------------------------------------
    # TRAIN TEST SPLIT
    # -----------------------------------------------------
    print("\nSplitting train/test dataset...")

    X_train, X_test, y_train, y_test = train_test_split(

        X,
        y,

        test_size=TEST_SIZE,

        random_state=RANDOM_STATE,
    )

    print(f"\nTrain Shape: {X_train.shape}")

    print(f"Test Shape: {X_test.shape}")

    # -----------------------------------------------------
    # BUILD MODEL
    # -----------------------------------------------------
    model = build_model()

    # -----------------------------------------------------
    # TRAIN
    # -----------------------------------------------------
    print("\nTraining started...\n")

    model.fit(
        X_train,
        y_train,
    )

    print("\nTraining completed.")

    # -----------------------------------------------------
    # PREDICTIONS
    # -----------------------------------------------------
    print("\nGenerating predictions...")

    predictions = model.predict(X_test)

    # -----------------------------------------------------
    # REVERSE LOG TRANSFORM
    # -----------------------------------------------------
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
    print("\nSaving model...")

    os.makedirs(
        MODEL_DIRECTORY,
        exist_ok=True,
    )

    joblib.dump(
        model,
        MODEL_PATH,
    )

    print(
        f"\n✅ Model saved successfully at:\n{MODEL_PATH}"
    )

    # -----------------------------------------------------
    # FEATURE IMPORTANCE
    # -----------------------------------------------------
    feature_importance = pd.DataFrame({

        "feature": X.columns,

        "importance": model.feature_importances_,
    })

    feature_importance = feature_importance.sort_values(
        by="importance",
        ascending=False,
    )

    print("\n========== TOP 20 FEATURES ==========\n")

    print(feature_importance.head(20))

    print("\n=====================================\n")

    return {
        "status": "success",
        "metrics": metrics,
    }


# =========================================================
# MAIN RUNNER
# =========================================================
if __name__ == "__main__":

    result = train_model()

    print("\n========== FINAL RESULT ==========\n")

    print(json.dumps(result, indent=4))

    print("\n==================================\n")
# Machine_Learning/train_model.py

import os
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

from Machine_Learning.preprocessing import preprocess_dataframe
from Machine_Learning.feature_engineering import create_features
from Machine_Learning.evaluation import evaluate_model
from Machine_Learning.constants import (
    TARGET_COLUMN,
    TEST_SIZE,
    RANDOM_STATE,
    MODEL_DIRECTORY,
    MODEL_PATH,
)


# =========================================================
# BASELINE TRAINING (SKLEARN ONLY FOR COMPARISON)
# =========================================================
def train_baseline_model():

    dataset_path = "Machine_Learning/datasets/training_dataset.csv"

    df = pd.read_csv(dataset_path)

    # -------------------------
    # CLEANING PIPELINE
    # -------------------------
    df = preprocess_dataframe(df)

    # -------------------------
    # FEATURE ENGINEERING
    # -------------------------
    df = create_features(df)

    # -------------------------
    # SPLIT FEATURES / TARGET
    # -------------------------
    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    # -------------------------
    # TRAIN / TEST SPLIT
    # -------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    # -------------------------
    # BASELINE MODEL
    # -------------------------
    model = RandomForestRegressor(
        n_estimators=200,
        random_state=RANDOM_STATE,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    # -------------------------
    # EVALUATION
    # -------------------------
    evaluate_model(y_test, predictions)

    # -------------------------
    # SAVE MODEL
    # -------------------------
    os.makedirs(MODEL_DIRECTORY, exist_ok=True)

    joblib.dump(model, MODEL_PATH)

    print("\n✅ Baseline model saved successfully at:", MODEL_PATH)


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    train_baseline_model()
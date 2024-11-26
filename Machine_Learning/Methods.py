import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
import joblib
from tortoise.transactions import in_transaction
from tortoise.functions import Avg
from datetime import datetime
import calendar
from Database_and_ORM.Database_Models import (
    ElectricityConsumption,
    QuestionnaireAnswers,
    User,
)
import json
from decouple import config
from os import path, makedirs
from time import time
import json
from fastapi import HTTPException, status

# ---------------------------------------------
# Method 1: Update Averages Dynamically
# ---------------------------------------------


async def load_gbm_config(
    config_path="Machine_Learning/Models/gbm_config.json",
):
    with open(config_path, "r") as config_file:
        return json.load(config_file)


async def update_averages_on_new_entry(user_id, year, month, new_consumption):
    """
    Updates rolling averages and trends for the given user's new electricity consumption entry.
    """

    async with in_transaction():
        # Fetch the user's 'nineteen' value and ZIP code
        user_questionaire_data = await QuestionnaireAnswers.get(
            user_id=user_id
        )
        user_data = await User.get(id=user_id)
        user_nineteen = user_questionaire_data.nineteen
        user_zip = await user_data.pin_code

        # Update averages for 'nineteen'
        nineteen_avg = (
            await ElectricityConsumption.filter(nineteen=user_nineteen)
            .annotate(avg_consumption=Avg("electricity_consumption"))
            .values("avg_consumption")
        )

        # Update averages for ZIP code
        zip_avg = (
            await ElectricityConsumption.filter(pin_code=user_zip)
            .annotate(avg_consumption=Avg("electricity_consumption"))
            .values("avg_consumption")
        )

        print(
            f"Updated averages for user {user_id}: {nineteen_avg}, {zip_avg}"
        )


# ---------------------------------------------
# Method 2: Retrain Model Periodically
# ---------------------------------------------


async def retrain_model():
    """
    Retrains the electricity consumption prediction model using HistGradientBoostingRegressor
    and updates status in Electricity_Model_Update_Status.json. Implements regularization
    and reduced model complexity to address overfitting. Includes MAE for precision evaluation.
    """

    model_dir = config("ELECTRICITY_CONSUMPTION_MODEL_PATH")
    model_path = path.join(model_dir, "Electricity_Consumption_Model.pkl")
    status_json_path = path.join(
        model_dir, "Electricity_Consumption_Model_Update_Status.json"
    )
    features_path = path.join(
        model_dir, "Electricity_Consumption_Model_Features.json"
    )

    if not path.exists(model_dir):
        makedirs(model_dir, exist_ok=True)

    start_time = time()
    max_duration = 7 * 3600  # 10 minutes for testing (adjust as needed)
    mae = float("inf")
    iteration = 0

    try:
        while mae > 5 and (time() - start_time) < max_duration:
            iteration += 1
            print(f"Retraining iteration {iteration}...")

            # Fetch data in batches
            offset = 0
            batch_size = 25
            merged_data = []

            while True:
                users_batch = (
                    await User.all()
                    .offset(offset)
                    .limit(batch_size)
                    .values("id", "pin_code")
                )
                if not users_batch:
                    break

                user_ids = [user["id"] for user in users_batch]
                consumption_batch = await ElectricityConsumption.filter(
                    user_id__in=user_ids
                ).values("user_id", "year", "month", "electricity_consumption")
                questionnaire_batch = await QuestionnaireAnswers.filter(
                    user_id__in=user_ids
                ).values(
                    "user_id",
                    "nineteen",
                    "one",
                    "two",
                    "three",
                    "seven",
                    "eighteen",
                )

                batch_data = pd.merge(
                    pd.DataFrame(consumption_batch),
                    pd.DataFrame(questionnaire_batch),
                    on="user_id",
                    how="left",
                )
                batch_data = pd.merge(
                    batch_data,
                    pd.DataFrame(users_batch),
                    left_on="user_id",
                    right_on="id",
                    how="left",
                )
                merged_data.append(batch_data)
                offset += batch_size

            if merged_data:
                final_data = pd.concat(merged_data, ignore_index=True)
            else:
                raise ValueError("No data available for training.")

            processed_data = feature_engineering(final_data)

            # Define features and target
            X = processed_data[
                [
                    "month",
                    "nineteen",
                    "zip_avg",
                    "zip_trend",
                    "nineteen_avg",
                    "nineteen_trend",
                    "prev_consumption",
                    "one",
                    "two",
                    "three",
                    "seven",
                    "eighteen",
                    "month_zip_interaction",  # New interaction
                    "month_nineteen_interaction",  # New interaction
                    "zip_trend_nineteen_trend_interaction",  # New interaction
                    "prev_consumption_month_interaction",  # New interaction
                ]
            ]
            y = processed_data["electricity_consumption"]

            X = pd.get_dummies(X, columns=["nineteen"], drop_first=True)
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Save feature names for future use
            feature_names = list(X_train.columns)
            with open(features_path, "w") as features_file:
                json.dump(feature_names, features_file)

            # HistGradientBoostingRegressor supports missing values natively
            gbm_config = await load_gbm_config()

            model = HistGradientBoostingRegressor(
                max_iter=gbm_config[
                    "n_estimators"
                ],  # Iterations analogous to n_estimators
                learning_rate=gbm_config["learning_rate"],
                max_depth=gbm_config["max_depth"],
                l2_regularization=gbm_config.get("l2_regularization", 0.0),
                max_leaf_nodes=gbm_config.get("max_leaf_nodes", 31),
                early_stopping=gbm_config.get("early_stopping", True),
                validation_fraction=gbm_config["validation_fraction"],
                tol=gbm_config["tol"],
                random_state=gbm_config["random_state"],
            )
            model.fit(X_train, y_train)

            y_train_pred = model.predict(X_train)
            y_val_pred = model.predict(X_val)

            train_mae = mean_absolute_error(y_train, y_train_pred)
            val_mae = mean_absolute_error(y_val, y_val_pred)

            print(
                f"Iteration {iteration}: Train MAE={train_mae:.4f}, Val MAE={val_mae:.4f}"
            )

            mae = val_mae

            joblib.dump(model, model_path)

            if mae <= 5:
                print("Model achieved target MAE. Training complete.")
                break

        duration = round(time() - start_time, 2)
        now = datetime.now()
        last_updated = now.strftime("%Y-%m-%d %H:%M:%S")

        status = {
            "last_updated": last_updated,
            "update_duration": f"{duration} seconds",
            "train_mae": round(train_mae, 4),
            "val_mae": round(val_mae, 4),
            "status": (
                "Training completed"
                if mae <= 5
                else "Stopped: Time limit reached"
            ),
            "iterations": iteration,
        }
        with open(status_json_path, "w") as status_file:
            json.dump(status, status_file, indent=4)

    except Exception as e:
        print(f"Error during training: {str(e)}")


# ---------------------------------------------
# Method 3: Feature Engineering
# ---------------------------------------------


def feature_engineering(data):
    """
    Applies feature engineering to prepare data for ML model training.
    """
    # Convert month names to numerical values
    data["month"] = data["month"].apply(
        lambda x: list(calendar.month_name).index(x)
    )

    # Add rolling averages for 'nineteen'
    data["nineteen_avg"] = data.groupby(["nineteen", "year"])[
        "electricity_consumption"
    ].transform("mean")
    data["nineteen_trend"] = data.groupby("nineteen")[
        "nineteen_avg"
    ].transform(lambda x: x.rolling(window=3, min_periods=1).mean())

    # Add ZIP code-level adjustments (fallback to nineteen)
    data["zip_avg"] = data.groupby(["pin_code", "year"])[
        "electricity_consumption"
    ].transform("mean")
    data["zip_avg"] = data["zip_avg"].fillna(data["nineteen_avg"])
    data["zip_trend"] = data.groupby("pin_code")["zip_avg"].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    data["zip_trend"] = data["zip_trend"].fillna(data["nineteen_trend"])

    # Create lag features for user-specific patterns
    data = data.sort_values(by=["user_id", "year", "month"])
    data["prev_consumption"] = data.groupby("user_id")[
        "electricity_consumption"
    ].shift(1)

    # Add interaction features
    data["month_zip_interaction"] = data["month"] * data["zip_avg"]
    data["month_nineteen_interaction"] = data["month"] * data["nineteen_avg"]
    data["zip_trend_nineteen_trend_interaction"] = (
        data["zip_trend"] * data["nineteen_trend"]
    )
    data["prev_consumption_month_interaction"] = (
        data["prev_consumption"] * data["month"]
    )

    # Drop rows with insufficient data for training
    data = data.dropna(subset=["prev_consumption"])

    return data


# ---------------------------------------------
# Method 4: Predict Consumption
# ---------------------------------------------


def predict_consumption(user_id, year, month, data, model):
    """
    Predicts electricity consumption for a user based on past data and locality trends.
    """
    user_data = data[
        (data["user_id"] == user_id)
        & (data["year"] == year)
        & (data["month"] == month)
    ]

    if user_data.empty:
        # Fallback to 'nineteen' and ZIP-level averages
        user_nineteen = data[data["user_id"] == user_id]["nineteen"].values[0]
        user_zip = data[data["user_id"] == user_id]["pin_code"].values[0]

        nineteen_avg = data[data["nineteen"] == user_nineteen][
            "nineteen_avg"
        ].mean()
        zip_avg = data[data["pin_code"] == user_zip]["zip_avg"].mean()

        return {
            "user_predicted_consumption": (
                zip_avg if not pd.isna(zip_avg) else nineteen_avg
            ),
            "locality_avg": nineteen_avg,
        }

    # Prepare input features
    user_data["month_zip_interaction"] = (
        user_data["month"] * user_data["zip_avg"]
    )
    user_data["month_nineteen_interaction"] = (
        user_data["month"] * user_data["nineteen_avg"]
    )
    user_data["zip_trend_nineteen_trend_interaction"] = (
        user_data["zip_trend"] * user_data["nineteen_trend"]
    )
    user_data["prev_consumption_month_interaction"] = (
        user_data["prev_consumption"] * user_data["month"]
    )

    X_input = user_data[
        [
            "month",
            "nineteen",
            "zip_avg",
            "zip_trend",
            "nineteen_avg",
            "nineteen_trend",
            "prev_consumption",
            "one",
            "two",
            "three",
            "seven",
            "eighteen",
            "month_zip_interaction",
            "month_nineteen_interaction",
            "zip_trend_nineteen_trend_interaction",
            "prev_consumption_month_interaction",
        ]
    ]
    X_input = pd.get_dummies(X_input, columns=["nineteen"], drop_first=True)

    # Predict
    prediction = model.predict(X_input)[0]
    return {
        "user_predicted_consumption": prediction,
        "locality_avg": user_data["nineteen_avg"].mean(),
    }

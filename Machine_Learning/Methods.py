import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error
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
        user_zip = await user_data.user.pin_code

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
    Retrains the electricity consumption prediction model and updates status in Electricity_Model_Update_Status.json.
    Implements regularization and reduced model complexity to address overfitting.
    """
    model_dir = config("ELECTRICITY_CONSUMPTION_MODEL_PATH")
    model_path = path.join(model_dir, "Electricity_Consumption_Model.pkl")
    status_json_path = path.join(
        model_dir, "Electricity_Model_Update_Status.json"
    )

    if not path.exists(model_dir):
        makedirs(model_dir, exist_ok=True)

    start_time = time()
    max_duration = 6 * 3600  # 6 hours in seconds
    rmse = float("inf")
    iteration = 0

    try:
        while rmse > 5 and (time() - start_time) < max_duration:
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
                ]
            ]
            y = processed_data["electricity_consumption"]

            X = pd.get_dummies(X, columns=["nineteen"], drop_first=True)
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)

            gbm_config = await load_gbm_config()

            model = GradientBoostingRegressor(
                n_estimators=gbm_config["n_estimators"],
                learning_rate=gbm_config["learning_rate"],
                max_depth=gbm_config["max_depth"],
                random_state=gbm_config["random_state"],
                subsample=gbm_config["subsample"],
                min_samples_split=gbm_config["min_samples_split"],
                min_samples_leaf=gbm_config["min_samples_leaf"],
                validation_fraction=gbm_config["validation_fraction"],
                n_iter_no_change=gbm_config["n_iter_no_change"],
                tol=gbm_config["tol"],
            )
            model.fit(X_train_scaled, y_train)

            y_train_pred = model.predict(X_train_scaled)
            y_val_pred = model.predict(X_val_scaled)

            train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
            val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))

            print(
                f"Iteration {iteration}: Train RMSE={train_rmse:.4f}, Val RMSE={val_rmse:.4f}"
            )

            rmse = val_rmse

            joblib.dump(model, model_path)

            if rmse <= 5:
                print("Model achieved target RMSE. Training complete.")
                break

        duration = round(time() - start_time, 2)
        now = datetime.now()
        last_updated = now.strftime("%Y-%m-%d %H:%M:%S")

        status = {
            "last_updated": last_updated,
            "update_duration": f"{duration} seconds",
            "train_rmse": round(train_rmse, 4),
            "val_rmse": round(val_rmse, 4),
            "status": (
                "Training completed"
                if rmse <= 5
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
        ]
    ]
    X_input = pd.get_dummies(X_input, columns=["nineteen"], drop_first=True)

    # Predict
    prediction = model.predict(X_input)[0]
    return {
        "user_predicted_consumption": prediction,
        "locality_avg": user_data["nineteen_avg"].mean(),
    }

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from skopt import BayesSearchCV
from skopt.space import Real, Integer
from sklearn.metrics import make_scorer
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
from sklearn.preprocessing import RobustScaler

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
        user_zip = user_data.pin_code

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


def train_val_mae_difference_score(estimator, X, y):
    """
    Custom scoring function to minimize the difference between Train MAE and Val MAE,
    while printing Train MAE, Validation MAE, and Percentage Accuracy after each fold.
    """
    # Split the data into training and validation
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Fit the estimator
    estimator.fit(X_train, y_train)

    # Predictions
    y_train_pred = estimator.predict(X_train)
    y_val_pred = estimator.predict(X_val)

    # Calculate Train MAE and Validation MAE
    train_mae = mean_absolute_error(np.expm1(y_train), np.expm1(y_train_pred))
    val_mae = mean_absolute_error(np.expm1(y_val), np.expm1(y_val_pred))

    # Calculate Percentage Accuracy
    mean_actual = np.mean(np.expm1(y_val))  # Mean of actual validation values
    percentage_accuracy = 100 - (val_mae / mean_actual * 100)

    # Print the results after each fold
    print(
        f"[CV] Train MAE={train_mae:.4f}, Validation MAE={val_mae:.4f}, "
        f"Difference={abs(train_mae - val_mae):.4f}, "
        f"Percentage Accuracy={percentage_accuracy:.2f}%"
    )

    # Return the absolute difference between Train MAE and Validation MAE as the scoring metric
    return abs(train_mae - val_mae)


async def retrain_model():
    """
    Retrains the electricity consumption prediction model using HistGradientBoostingRegressor
    with Bayesian optimization for parameter tuning.
    """
    model_dir = config("ELECTRICITY_CONSUMPTION_MODEL_PATH")
    model_path = path.join(model_dir, "Electricity_Consumption_Model.pkl")
    status_json_path = path.join(
        model_dir, "Electricity_Consumption_Model_Update_Status.json"
    )
    features_path = path.join(
        model_dir, "Electricity_Consumption_Model_Features.json"
    )
    gbm_config_path = "Machine_Learning/Models/gbm_config.json"

    if not path.exists(model_dir):
        makedirs(model_dir, exist_ok=True)

    start_time = time()
    max_duration = 7 * 3600  # 7 hours for training
    mae = float("inf")
    iteration = 0

    try:
        while mae > 3 and (time() - start_time) < max_duration:
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

            print(f"Final data shape: {final_data.shape}")
            processed_data = feature_engineering(final_data)

            if processed_data.empty:
                raise ValueError(
                    "Processed data is empty after feature engineering."
                )

            # Define features and target
            X = processed_data[
                [
                    "month",
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
                    "month_sin",
                    "month_cos",
                ]
            ]
            y = processed_data["electricity_consumption"]

            print(f"Target variable (y) shape: {y.shape}")

            y = np.log1p(y)
            scaler = RobustScaler()
            X_scaled = scaler.fit_transform(X)

            param_space = {
                "max_iter": Integer(500, 5000),
                "learning_rate": Real(0.001, 0.5, prior="log-uniform"),
                "max_depth": Integer(5, 12),
                "min_samples_leaf": Integer(6, 25),
                "l2_regularization": Real(0.01, 0.3, prior="log-uniform"),
                "max_bins": Integer(2, 255),
            }

            gbm_config = await load_gbm_config()

            base_model = HistGradientBoostingRegressor(
                loss="absolute_error",
                tol=gbm_config["tol"],
                random_state=gbm_config["random_state"],
            )

            def scoring_function(estimator, X_subset, y_subset=y):
                return train_val_mae_difference_score(
                    estimator, X_subset, y_subset
                )

            bayes_search = BayesSearchCV(
                base_model,
                search_spaces=param_space,
                scoring=scoring_function,
                n_iter=100,
                cv=5,
                verbose=2,
                random_state=42,
            )

            print(f"X_scaled shape: {X_scaled.shape}, y shape: {y.shape}")
            bayes_search.fit(X_scaled, y)

            model = bayes_search.best_estimator_
            print(f"Best parameters: {bayes_search.best_params_}")

            # Update gbm_config.json with the best parameters
            gbm_config.update(bayes_search.best_params_)
            with open(gbm_config_path, "w") as config_file:
                json.dump(gbm_config, config_file, indent=4)
            print(f"Updated {gbm_config_path} with best parameters.")

            # Evaluate after Bayesian optimization
            y_train_pred = model.predict(X_scaled)
            train_mae = mean_absolute_error(
                np.expm1(y), np.expm1(y_train_pred)
            )
            mean_actual = np.mean(np.expm1(y))
            percentage_accuracy = 100 - (train_mae / mean_actual * 100)

            # Split for validation evaluation
            X_train, X_val, y_train_split, y_val_split = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            y_val_pred = model.predict(X_val)
            val_mae = mean_absolute_error(
                np.expm1(y_val_split), np.expm1(y_val_pred)
            )
            train_val_difference = abs(train_mae - val_mae)

            # Log after Bayesian tuning
            print(
                f"Bayesian Parameter Tuning - Train MAE={train_mae:.4f}, "
                f"Validation MAE={val_mae:.4f}, "
                f"Difference={train_val_difference:.4f}, "
                f"Percentage Accuracy={percentage_accuracy:.2f}%"
            )

            # Final evaluation for the iteration
            print(
                f"Iteration {iteration}: "
                f"Train MAE={train_mae:.4f}, Validation MAE={val_mae:.4f}, "
                f"Difference={train_val_difference:.4f}, Percentage Accuracy={percentage_accuracy:.2f}%"
            )

            mae = train_mae

            joblib.dump(model, model_path)

            if mae <= 3:
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
            "train_val_difference": round(train_val_difference, 4),
            "percentage_accuracy": round(percentage_accuracy, 2),
            "status": (
                "Training completed"
                if mae <= 3
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
    # Ensure the target column is not accidentally dropped
    if "electricity_consumption" not in data.columns:
        raise ValueError(
            "Target column 'electricity_consumption' is missing in input data."
        )

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

    # Add cyclical encoding for months
    data["month_sin"] = np.sin(2 * np.pi * data["month"] / 12)
    data["month_cos"] = np.cos(2 * np.pi * data["month"] / 12)

    # Drop rows with insufficient data for training
    data = data.dropna(subset=["prev_consumption"])

    return data

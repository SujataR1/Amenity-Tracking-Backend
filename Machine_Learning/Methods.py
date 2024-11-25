import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error
import joblib
from tortoise.transactions import in_transaction
from tortoise.expressions import Avg
from datetime import datetime
import calendar
from Database_and_ORM.Database_Models import (
    ElectricityConsumption,
    QuestionnaireAnswers,
    User,
    Admin,
)
from decouple import config
from os import path, makedirs
import time
import json
from fastapi import HTTPException, status

# ---------------------------------------------
# Method 1: Update Averages Dynamically
# ---------------------------------------------


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


async def retrain_model(payload: dict):
    """
    Retrains the electricity consumption prediction model and updates status in Electricity_Model_Update_Status.json.
    """
    # Paths
    admin_id = payload.get("user_id")
    admin = await Admin.get_or_none(id=admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins are authorized to view model training status.",
        )
    model_dir = config("ELECTRICITY_CONSUMPTION_MODEL_PATH")
    model_path = path.join(model_dir, "Electricity_Consumption_Model.pkl")
    status_json_path = path.join(
        model_dir, "Electricity_Model_Update_Status.json"
    )

    # Ensure the directory exists
    if not path.exists(model_dir):
        makedirs(model_dir, exist_ok=True)

    # Initialize or update status file to reflect "Starting"
    if not path.exists(status_json_path):
        with open(status_json_path, "w") as status_file:
            json.dump(
                {
                    "last_updated": None,
                    "update_duration": None,
                    "days_since_last_update": None,
                    "mse": None,
                    "rmse": None,
                    "status": "Starting model training",
                },
                status_file,
                indent=4,
            )
    else:
        with open(status_json_path, "r+") as status_file:
            status = json.load(status_file)
            status["status"] = "Starting model training"
            status_file.seek(0)
            json.dump(status, status_file, indent=4)
            status_file.truncate()

    # Start tracking the time for retraining
    start_time = time()

    # Update status to "In Progress"
    with open(status_json_path, "r+") as status_file:
        status = json.load(status_file)
        status["status"] = "Model training in progress"
        status_file.seek(0)
        json.dump(status, status_file, indent=4)
        status_file.truncate()

    try:
        # Fetch updated data
        consumption_data = await ElectricityConsumption.all().values(
            "user_id", "year", "month", "electricity_consumption"
        )
        questionnaire_data = await QuestionnaireAnswers.all().values(
            "user_id", "nineteen", "one", "two", "three", "seven", "eighteen"
        )
        user_data = await User.all().values("id", "pin_code")

        # Merge and process data
        merged_data = pd.merge(
            pd.DataFrame(consumption_data),
            pd.DataFrame(questionnaire_data),
            on="user_id",
            how="left",
        )
        merged_data = pd.merge(
            merged_data,
            pd.DataFrame(user_data),
            left_on="user_id",
            right_on="id",
            how="left",
        )
        processed_data = feature_engineering(merged_data)

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

        # One-hot encode categorical features
        X = pd.get_dummies(X, columns=["nineteen"], drop_first=True)

        # Train the model
        model = GradientBoostingRegressor(
            n_estimators=500, learning_rate=0.1, max_depth=5, random_state=42
        )
        model.fit(X, y)

        # Calculate MSE and RMSE
        y_pred = model.predict(X)
        mse = mean_squared_error(y, y_pred)
        rmse = mse**0.5

        # Save the model
        joblib.dump(model, model_path)

        # End tracking the time for retraining
        end_time = time()
        duration = round(end_time - start_time, 2)  # Duration in seconds

        # Update the status JSON to "Trained"
        now = datetime.now()
        last_updated = now.strftime("%Y-%m-%d %H:%M:%S")
        days_since_last_update = None  # First model training

        if path.exists(status_json_path):
            with open(status_json_path, "r") as status_file:
                previous_status = json.load(status_file)
                if previous_status.get("last_updated"):
                    last_update_date = datetime.strptime(
                        previous_status["last_updated"], "%Y-%m-%d %H:%M:%S"
                    )
                    days_since_last_update = (now - last_update_date).days

        # Save final updated status
        status = {
            "last_updated": last_updated,
            "update_duration": f"{duration} seconds",
            "days_since_last_update": days_since_last_update,
            "mse": round(mse, 4),
            "rmse": round(rmse, 4),
            "status": "Model training completed",
        }
        with open(status_json_path, "w") as status_file:
            json.dump(status, status_file, indent=4)

        print(f"Model retrained and saved to {model_path}")
        print(f"MSE: {mse:.4f}, RMSE: {rmse:.4f}")
        return model_path

    except Exception as e:
        # Update status to "Failed" in case of an error
        with open(status_json_path, "r+") as status_file:
            status = json.load(status_file)
            status["status"] = f"Model training failed: {str(e)}"
            status_file.seek(0)
            json.dump(status, status_file, indent=4)
            status_file.truncate()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training failed: {str(e)}",
        )


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
    data["zip_avg"].fillna(data["nineteen_avg"], inplace=True)
    data["zip_trend"] = data.groupby("pin_code")["zip_avg"].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    data["zip_trend"].fillna(data["nineteen_trend"], inplace=True)

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

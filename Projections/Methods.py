import pandas as pd
import os
from datetime import datetime
import joblib
from sklearn.metrics import mean_squared_error
from tortoise.functions import Avg
from Machine_Learning.Methods import feature_engineering
from Database_and_ORM.Database_Models import (
    ElectricityConsumption,
    QuestionnaireAnswers,
    User,
)
from fastapi import HTTPException, status


async def predict_consumption(user_id, month, year, payload: dict):
    """
    Predicts electricity consumption for a user based on their history, locality trends,
    and questionnaire answers.
    """
    user_id = payload.get("user_id")
    user = await User.get_or_none(id=user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please login to get projection data",
        )
    # Paths to model and metadata
    model_dir = os.getenv("ELECTRICITY_CONSUMPTION_MODEL_PATH")
    model_path = os.path.join(model_dir, "Electricity_Consumption_Model.pkl")

    # Check if the model exists
    if not os.path.exists(model_path):
        raise FileNotFoundError("Model not found. Retrain the model first.")

    # Load the trained model
    model = joblib.load(model_path)

    # Fetch data for the given user
    try:
        # Fetch user's questionnaire answers
        user_questionnaire = await QuestionnaireAnswers.get(user_id=user_id)
        # Fetch user's ZIP code and locality
        user_data = await User.get(id=user_id).values("pin_code", "id")

        # Prepare data for predictions
        questionnaire_data = {
            "nineteen": user_questionnaire.nineteen,
            "one": user_questionnaire.one,
            "two": user_questionnaire.two,
            "three": user_questionnaire.three,
            "seven": user_questionnaire.seven,
            "eighteen": user_questionnaire.eighteen,
        }

        # Convert month name to number
        month_num = datetime.strptime(month, "%B").month

        # Calculate locality averages
        zip_avg = (
            await ElectricityConsumption.filter(
                pin_code=user_data["pin_code"], year=year
            )
            .annotate(avg_consumption=Avg("electricity_consumption"))
            .values_list("avg_consumption", flat=True)
        )
        nineteen_avg = (
            await ElectricityConsumption.filter(
                nineteen=user_questionnaire.nineteen, year=year
            )
            .annotate(avg_consumption=Avg("electricity_consumption"))
            .values_list("avg_consumption", flat=True)
        )

        zip_avg = zip_avg[0] if zip_avg else None
        nineteen_avg = nineteen_avg[0] if nineteen_avg else None

        # Previous consumption
        previous_consumption = await ElectricityConsumption.filter(
            user_id=user_id, year=year, month=month
        ).values_list("electricity_consumption", flat=True)
        previous_consumption = (
            previous_consumption[0] if previous_consumption else None
        )

        # Create input data for prediction
        input_data = pd.DataFrame(
            [
                {
                    "month": month_num,
                    "nineteen": user_questionnaire.nineteen,
                    "zip_avg": zip_avg,
                    "nineteen_avg": nineteen_avg,
                    "prev_consumption": previous_consumption,
                    **questionnaire_data,
                }
            ]
        )

        # One-hot encode 'nineteen'
        input_data = pd.get_dummies(
            input_data, columns=["nineteen"], drop_first=True
        )

        # Align input data with model features
        all_features = model.feature_names_in_
        input_data = input_data.reindex(columns=all_features, fill_value=0)

        # Make the prediction
        predicted_consumption = model.predict(input_data)[0]

        # Calculate locality projection
        locality_projection = nineteen_avg or zip_avg or 0  # Fallback logic

        return {
            "user_id": user_id,
            "month": month,
            "year": year,
            "projected_consumption": round(predicted_consumption, 2),
            "locality_projection": (
                round(locality_projection, 2) if locality_projection else None
            ),
        }

    except Exception as e:
        raise Exception(f"Error during prediction: {str(e)}")

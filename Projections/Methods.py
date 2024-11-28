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
import json
from decouple import config
import torch
from Machine_Learning.Methods import ElectricityConsumptionModel


async def predict_consumption(month, year, payload: dict):
    """
    Predicts electricity consumption for a user based on their history, locality trends,
    and questionnaire answers using a PyTorch model.
    """
    user_id = payload.get("user_id")
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please login to get projection data",
        )

    # Paths to model and metadata
    model_dir = config("ELECTRICITY_CONSUMPTION_MODEL_PATH")
    model_path = os.path.join(model_dir, "Electricity_Consumption_Model.pt")
    features_path = os.path.join(
        model_dir, "Electricity_Consumption_Model_Features.json"
    )

    # Check if the model exists
    if not os.path.exists(model_path):
        raise FileNotFoundError("Model not found. Retrain the model first.")

    # Check if feature names file exists
    if not os.path.exists(features_path):
        raise FileNotFoundError(
            "Feature names file not found. Retrain the model and save feature names."
        )

    # Define the model architecture
    input_dim = len(json.load(open(features_path)))  # Read feature count
    hidden_dim1 = 128  # Should match training setup
    hidden_dim2 = 64
    model = ElectricityConsumptionModel(input_dim, hidden_dim1, hidden_dim2)

    # Load the trained model weights
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

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

        month_num = datetime.strptime(month, "%B").month

        # Calculate locality averages
        zip_avg = (
            await ElectricityConsumption.filter(
                user__pin_code=user_data["pin_code"], year=year
            )
            .annotate(avg_consumption=Avg("electricity_consumption"))
            .values_list("avg_consumption", flat=True)
        )
        nineteen_avg = (
            await ElectricityConsumption.filter(
                user__questionnaire_answers__nineteen=user_questionnaire.nineteen,
                year=year,
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

        # Add interaction features
        input_data["month_zip_interaction"] = (
            input_data["month"] * input_data["zip_avg"]
        )
        input_data["month_nineteen_interaction"] = (
            input_data["month"] * input_data["nineteen_avg"]
        )
        input_data["zip_trend_nineteen_trend_interaction"] = (
            input_data["zip_avg"] * input_data["nineteen_avg"]
        )
        input_data["prev_consumption_month_interaction"] = (
            input_data["prev_consumption"] * input_data["month"]
        )

        # One-hot encode 'nineteen'
        input_data = pd.get_dummies(
            input_data, columns=["nineteen"], drop_first=True
        )

        # Align input data with saved feature names
        with open(features_path, "r") as f:
            all_features = json.load(f)
        input_data = input_data.reindex(columns=all_features, fill_value=0)

        # Convert to PyTorch tensor
        input_tensor = torch.tensor(input_data.values, dtype=torch.float32).to(
            device
        )

        # Make the prediction
        with torch.no_grad():
            predicted_consumption = model(input_tensor).cpu().numpy()[0][0]

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

import pandas as pd
import os
from datetime import datetime
from sklearn.metrics import mean_squared_error
from Database_and_ORM.Database_Models import (
    QuestionnaireAnswers,
    User,
)
from fastapi import HTTPException, status
import json
from decouple import config
import torch
from Machine_Learning.Methods import ElectricityConsumptionModel
import numpy as np
import pickle

async def predict_consumption(month, year, payload: dict):
    """
    Predicts electricity consumption for a user based on their history, locality trends,
    and questionnaire answers using the trained PyTorch model.
    """
    user_id = payload.get("user_id")
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please login to get projection data",
        )

    # Paths to model, scaler, and metadata
    model_dir = config("ELECTRICITY_CONSUMPTION_MODEL_PATH")
    model_path = os.path.join(model_dir, "Electricity_Consumption_Model.pt")
    features_path = os.path.join(model_dir, "Electricity_Consumption_Model_Features.json")
    user_id_mapping_path = os.path.join(model_dir, "User_ID_Mapping.pkl")
    scaler_path = os.path.join(model_dir, "Scaler.pkl")

    # Check if the model exists
    if not os.path.exists(model_path):
        raise FileNotFoundError("Model not found. Retrain the model first.")

    # Check if feature names file exists
    if not os.path.exists(features_path):
        raise FileNotFoundError("Feature names file not found. Retrain the model and save feature names.")

    # Check if user ID mapping exists
    if not os.path.exists(user_id_mapping_path):
        raise FileNotFoundError("User ID mapping file not found. Retrain the model to generate it.")

    # Check if scaler file exists
    if not os.path.exists(scaler_path):
        raise FileNotFoundError("Scaler file not found. Retrain the model to generate it.")

    # Load metadata and model components
    with open(features_path, "r") as f:
        all_features = json.load(f)

    with open(user_id_mapping_path, "rb") as f:
        user_id_mapping = pickle.load(f)

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    # Map user ID
    if user_id not in user_id_mapping:
        raise ValueError("User ID not found in the trained model. Retrain the model to include this user.")

    user_mapped_id = user_id_mapping[user_id]

    # Define the model architecture
    input_dim = len(all_features)  # Feature count
    model = ElectricityConsumptionModel(
        num_users=len(user_id_mapping), 
        input_dim=input_dim, 
        hidden_dim1=128,  # These should match the best params from retraining
        hidden_dim2=64, 
        embedding_dim=32,  # Adjust based on your embedding dimension
        dropout_rate=0.3  # Adjust based on the dropout rate in your model
    )

    # Load the trained model weights
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    try:
        # Fetch user's questionnaire answers
        user_questionnaire = await QuestionnaireAnswers.get(user_id=user_id)
        # Fetch user's ZIP code
        user_data = await User.get(id=user_id).values("pin_code", "id")

        # Prepare data for predictions
        questionnaire_data = {
            "one": user_questionnaire.one,
            "two": user_questionnaire.two,
            "three": user_questionnaire.three,
            "four": int(user_questionnaire.four),
            "five": int(user_questionnaire.five),
            "six": int(user_questionnaire.six),
            "seven": int(user_questionnaire.seven),
            "eight": int(user_questionnaire.eight),
            "nine": int(user_questionnaire.nine),
            "ten": int(user_questionnaire.ten),
            "eleven": int(user_questionnaire.eleven),
            "twelve": int(user_questionnaire.twelve),
            "thirteen": int(user_questionnaire.thirteen),
            "fourteen": float(user_questionnaire.fourteen),
            "fifteen": int(user_questionnaire.fifteen),
            "sixteen": int(user_questionnaire.sixteen),
            "eighteen": user_questionnaire.eighteen,
        }

        # Encode month as one-hot
        month_num = datetime.strptime(month, "%B").month
        month_data = {f"month_{i}": 1 if i == month_num else 0 for i in range(1, 13)}

        # One-hot encode 'nineteen' (climate)
        climate = str(user_questionnaire.nineteen)
        nineteen_data = {f"climate_{climate}": 1}

        # One-hot encode 'seventeen' (vacation months)
        seventeen_months = user_questionnaire.seventeen
        seventeen_data = {f"vacation_month_{m}": (1 if m in seventeen_months else 0) for m in range(1, 13)}

        # Combine all features into a single dictionary
        input_data = pd.DataFrame(
            [
                {
                    "year": int(year),
                    "pin_code": user_data["pin_code"],
                    **questionnaire_data,
                    **month_data,
                    **nineteen_data,
                    **seventeen_data,
                }
            ]
        )

        # Align input data with saved feature names
        input_data = input_data.reindex(columns=all_features, fill_value=0)

        # Scale features
        input_data_scaled = scaler.transform(input_data)

        # Convert to PyTorch tensors
        user_id_tensor = torch.tensor([user_mapped_id], dtype=torch.long).to(device)
        feature_tensor = torch.tensor(input_data_scaled, dtype=torch.float32).to(device)

        # Make the prediction
        with torch.no_grad():
            predicted_consumption = model(user_id_tensor, feature_tensor).cpu().numpy()[0][0]

        # Convert values to standard Python types for JSON serialization
        predicted_consumption = float(np.expm1(predicted_consumption))  # Revert log1p transformation

        # Return the result with serialized types
        return {
            "user_id": user_id,
            "month": month,
            "year": year,
            "projected_consumption": round(predicted_consumption, 2),
        }

    except Exception as e:
        raise Exception(f"Error during prediction: {str(e)}")

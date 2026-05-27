import pandas as pd
import numpy as np
import json
from os import path
from datetime import datetime
import joblib

from fastapi import HTTPException, status

from Database_and_ORM.Database_Models import QuestionnaireAnswers, User
from Machine_Learning.Data_Schemas import ResourceTypeEnum
from Machine_Learning.feature_engineering import create_features
from Machine_Learning.preprocessing import preprocess_dataframe


# =========================================================
# MAIN PREDICTION FUNCTION
# =========================================================
async def predict_consumption(
    resource_type: ResourceTypeEnum,
    month,
    year: int,
    payload: dict,
):

    # -------------------------
    # Normalize resource type
    # -------------------------
    resource_type = resource_type.value

    # =====================================================
    # LOAD CONFIG JSON (SAFE FIX)
    # =====================================================
    config_path = "Machine_Learning/Machine_Learning_Parameter_Schemas.json"

    if not path.exists(config_path):
        raise HTTPException(
            status_code=500,
            detail="Config file not found"
        )

    with open(config_path, "r") as file:
        machine_learning_parameter_schemas = json.load(file)

    config = machine_learning_parameter_schemas.get(resource_type)

    if not config:
        raise HTTPException(
            status_code=400,
            detail=f"Configuration missing for {resource_type}"
        )

    # =====================================================
    # BUILD PATHS
    # =====================================================
    model_dir = config["Directory_Path"]

    model_path = path.join(model_dir, config["Trained_Model_Name"])
    features_path = path.join(model_dir, config["Features_File_Name"])

    # =====================================================
    # USER VALIDATION
    # =====================================================
    user_id = payload.get("user_id")

    user = await User.get_or_none(id=user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found / invalid session"
        )

    # =====================================================
    # FILE CHECK (REAL ROOT FIX)
    # =====================================================
    if not path.exists(model_path):
        raise HTTPException(
            status_code=500,
            detail=f"Model file missing: {model_path}"
        )

    if not path.exists(features_path):
        raise HTTPException(
            status_code=500,
            detail=f"Features file missing: {features_path}"
        )

    # =====================================================
    # LOAD MODEL
    # =====================================================
    model = joblib.load(model_path)

    # =====================================================
    # LOAD FEATURE LIST (FIX JSON BUG)
    # =====================================================
    with open(features_path, "r") as f:
        all_features = json.load(f)

    # =====================================================
    # GET USER QUESTIONNAIRE
    # =====================================================
    user_questionnaire = await QuestionnaireAnswers.get(user_id=user_id)

    # =====================================================
    # FIX MONTH INPUT SAFELY
    # =====================================================
    if isinstance(month, int):
        month_num = month
    else:
        try:
            month_num = datetime.strptime(month, "%B").month
        except:
            month_num = int(month)

    # =====================================================
    # BUILD INPUT DATA
    # =====================================================
    input_data = {
        "year": int(year),
        "month": month_num,

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
        "seventeen": str(user_questionnaire.seventeen),
        "eighteen": int(user_questionnaire.eighteen),
        "nineteen": str(user_questionnaire.nineteen),
    }

    df = pd.DataFrame([input_data])

    # =====================================================
    # PIPELINE
    # =====================================================
    df = preprocess_dataframe(df)
    df = create_features(df)

    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    for col in [
        "last_month_consumption",
        "avg_last_3_months",
        "avg_last_6_months",
        "consumption_growth_rate",
        "yearly_avg_consumption",
    ]:
        df[col] = 0

    df = pd.get_dummies(df, columns=["nineteen", "seventeen"], drop_first=False)

    df = df.reindex(columns=all_features, fill_value=0)

    # =====================================================
    # PREDICTION
    # =====================================================
    prediction = model.predict(df)

    predicted_consumption = float(np.expm1(prediction[0]))
    estimated_bill = predicted_consumption * 8

    return {
        "resource_type": resource_type,
        "user_id": str(user_id),
        "month": month_num,
        "year": year,
        "projected_consumption": round(predicted_consumption, 2),
        "estimated_bill": round(estimated_bill, 2),
    }
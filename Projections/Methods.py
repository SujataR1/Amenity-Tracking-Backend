# Projections/Methods.py

import pandas as pd
import numpy as np
import json
from os import path
from datetime import datetime
import joblib

from fastapi import HTTPException, status

from Database_and_ORM.Database_Models import (
    QuestionnaireAnswers,
    User,
)

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

    # =====================================================
    # NORMALIZE RESOURCE TYPE
    # =====================================================
    resource_type = resource_type.value

    # =====================================================
    # LOAD CONFIG
    # =====================================================
    config_path = "Machine_Learning/Machine_Learning_Parameter_Schemas.json"

    if not path.exists(config_path):
        raise HTTPException(
            status_code=500,
            detail="Machine learning config file not found",
        )

    with open(config_path, "r") as file:
        configs = json.load(file)

    config = configs.get(resource_type)

    if not config:
        raise HTTPException(
            status_code=400,
            detail=f"No configuration found for {resource_type}",
        )

    # =====================================================
    # BUILD MODEL PATHS
    # =====================================================
    model_dir = config["Directory_Path"]

    model_path = path.join(
        model_dir,
        config["Trained_Model_Name"],
    )

    features_path = path.join(
        model_dir,
        config["Features_File_Name"],
    )

    # =====================================================
    # VALIDATE USER
    # =====================================================
    user_id = payload.get("user_id")

    user = await User.get_or_none(id=user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user",
        )

    # =====================================================
    # CHECK MODEL FILES
    # =====================================================
    if not path.exists(model_path):
        raise HTTPException(
            status_code=500,
            detail=f"Model file missing: {model_path}",
        )

    if not path.exists(features_path):
        raise HTTPException(
            status_code=500,
            detail=f"Features file missing: {features_path}",
        )

    # =====================================================
    # LOAD MODEL
    # =====================================================
    model = joblib.load(model_path)

    # =====================================================
    # LOAD FEATURES
    # =====================================================
    with open(features_path, "r") as f:
        features_data = json.load(f)

    # FIXED ROOT ISSUE
    if isinstance(features_data, dict):
        all_features = features_data.get("features", [])
    else:
        all_features = features_data

    if not isinstance(all_features, list):
        raise HTTPException(
            status_code=500,
            detail="Invalid features file format",
        )

    # =====================================================
    # GET QUESTIONNAIRE ANSWERS
    # =====================================================
    user_questionnaire = await QuestionnaireAnswers.get_or_none(
        user_id=user_id
    )

    if not user_questionnaire:
        raise HTTPException(
            status_code=404,
            detail="Questionnaire answers not found",
        )

    # =====================================================
    # CONVERT MONTH TO NUMBER
    # =====================================================
    try:
        if isinstance(month, int):
            month_num = month
        else:
            month_num = datetime.strptime(
                month,
                "%B"
            ).month

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid month format",
        )

    # =====================================================
    # BUILD INPUT DATA
    # =====================================================
    input_data = {
        "year": int(year),
        "month": month_num,

        "num_people": user_questionnaire.num_people,
        "num_children": user_questionnaire.num_children,
        "bedrooms": user_questionnaire.bedrooms,

        "has_ac": int(user_questionnaire.has_ac),
        "has_geyser": int(user_questionnaire.has_geyser),
        "has_iron": int(user_questionnaire.has_iron),

        "has_washing_machine": int(
            user_questionnaire.has_washing_machine
        ),

        "has_dishwasher": int(
            user_questionnaire.has_dishwasher
        ),

        "has_induction": int(
            user_questionnaire.has_induction
        ),

        "has_microwave": int(
            user_questionnaire.has_microwave
        ),

        "has_kettle": int(
            user_questionnaire.has_kettle
        ),

        "has_vacuum": int(
            user_questionnaire.has_vacuum
        ),

        "has_room_heater": int(
            user_questionnaire.has_room_heater
        ),

        "home_area": float(
            user_questionnaire.home_area
        ),

        "has_pool": int(
            user_questionnaire.has_pool
        ),

        "has_garden": int(
            user_questionnaire.has_garden
        ),

        "vacation_month": str(
            user_questionnaire.vacation_month
        ),

        "vacation_days": int(
            user_questionnaire.vacation_days
        ),

        "climate": str(
            user_questionnaire.climate
        ),

        # historical defaults
        "billing_days": 30,
    }

    # =====================================================
    # DATAFRAME
    # =====================================================
    df = pd.DataFrame([input_data])

    # =====================================================
    # PREPROCESSING
    # =====================================================
    df = preprocess_dataframe(df)

    # =====================================================
    # FEATURE ENGINEERING
    # =====================================================
    df = create_features(df)

    # =====================================================
    # CYCLICAL MONTH FEATURES
    # =====================================================
    df["month_sin"] = np.sin(
        2 * np.pi * df["month"] / 12
    )

    df["month_cos"] = np.cos(
        2 * np.pi * df["month"] / 12
    )

    # =====================================================
    # DEFAULT HISTORICAL FEATURES
    # =====================================================
    historical_columns = [
        "last_month_consumption",
        "avg_last_3_months",
        "avg_last_6_months",
        "consumption_growth_rate",
        "yearly_avg_consumption",
    ]

    for col in historical_columns:
        if col not in df.columns:
            df[col] = 0

    # =====================================================
    # ENCODE CATEGORICALS
    # =====================================================
    categorical_columns = []

    if "climate" in df.columns:
        categorical_columns.append("climate")

    if "vacation_month" in df.columns:
        categorical_columns.append("vacation_month")

    if categorical_columns:
        df = pd.get_dummies(
            df,
            columns=categorical_columns,
            drop_first=False,
        )

    # =====================================================
    # ALIGN FEATURES
    # =====================================================
    df = df.reindex(
        columns=all_features,
        fill_value=0,
    )

    # =====================================================
    # PREDICTION
    # =====================================================
    prediction = model.predict(df)

    predicted_consumption = float(
        np.expm1(prediction[0])
    )

    estimated_bill = predicted_consumption * 8

    # =====================================================
    # RESPONSE
    # =====================================================
    return {
        "resource_type": resource_type,
        "user_id": str(user_id),
        "month": month_num,
        "year": year,
        "projected_consumption": round(
            predicted_consumption,
            2,
        ),
        "estimated_bill": round(
            estimated_bill,
            2,
        ),
    }
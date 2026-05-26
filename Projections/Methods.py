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

from Machine_Learning.Data_Schemas import (
    ResourceTypeEnum,
)

from Machine_Learning.feature_engineering import (
    create_features,
)

from Machine_Learning.preprocessing import (
    preprocess_dataframe,
)


# =========================================================
# MAIN PREDICTION FUNCTION
# =========================================================
async def predict_consumption(
    resource_type: ResourceTypeEnum,
    month: str,
    year: int,
    payload: dict,
):

    # =====================================================
    # RESOURCE TYPE
    # =====================================================
    resource_type = resource_type.value

    # =====================================================
    # LOAD CONFIG
    # =====================================================
    with open(
        "Machine_Learning/Machine_Learning_Parameter_Schemas.json",
        "r",
    ) as file:

        machine_learning_parameter_schemas = json.load(
            file.read()
        )

    config = machine_learning_parameter_schemas.get(
        resource_type
    )

    if not config:

        raise ValueError(
            f"Configuration for resource type "
            f"'{resource_type}' not found."
        )

    # =====================================================
    # PATHS
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

    target_column = config["Column_Name"]

    # =====================================================
    # USER
    # =====================================================
    user_id = payload.get("user_id")

    user = await User.get_or_none(
        id=user_id
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please login to get projection data",
        )

    # =====================================================
    # FILE EXISTENCE CHECK
    # =====================================================
    if not path.exists(model_path):

        raise FileNotFoundError(
            f"{resource_type} model not found."
        )

    if not path.exists(features_path):

        raise FileNotFoundError(
            f"{resource_type} feature file not found."
        )

    # =====================================================
    # LOAD MODEL
    # =====================================================
    model = joblib.load(model_path)

    # =====================================================
    # LOAD FEATURE NAMES
    # =====================================================
    with open(features_path, "r") as f:

        all_features = json.load(f)

    try:

        # =================================================
        # LOAD QUESTIONNAIRE
        # =================================================
        user_questionnaire = (
            await QuestionnaireAnswers.get(
                user_id=user_id
            )
        )

        # =================================================
        # MONTH NUMBER
        # =================================================
        month_num = datetime.strptime(
            month,
            "%B",
        ).month

        # =================================================
        # INPUT DATA
        # =================================================
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

            "fourteen": float(
                user_questionnaire.fourteen
            ),

            "fifteen": int(
                user_questionnaire.fifteen
            ),

            "sixteen": int(
                user_questionnaire.sixteen
            ),

            "seventeen": str(
                user_questionnaire.seventeen
            ),

            "eighteen": int(
                user_questionnaire.eighteen
            ),

            "nineteen": str(
                user_questionnaire.nineteen
            ),
        }

        # =================================================
        # DATAFRAME
        # =================================================
        df = pd.DataFrame([input_data])

        # =================================================
        # PREPROCESSING
        # =================================================
        df = preprocess_dataframe(df)

        # =================================================
        # FEATURE ENGINEERING
        # =================================================
        df = create_features(df)

        # =================================================
        # CYCLICAL MONTH FEATURES
        # =================================================
        df["month_sin"] = np.sin(
            2 * np.pi * df["month"] / 12
        )

        df["month_cos"] = np.cos(
            2 * np.pi * df["month"] / 12
        )

        # =================================================
        # HISTORICAL DEFAULTS
        # =================================================
        historical_columns = [

            "last_month_consumption",

            "avg_last_3_months",

            "avg_last_6_months",

            "consumption_growth_rate",

            "yearly_avg_consumption",
        ]

        for col in historical_columns:

            df[col] = 0

        # =================================================
        # ONE HOT ENCODING
        # =================================================
        df = pd.get_dummies(
            df,
            columns=[
                "nineteen",
                "seventeen",
            ],
            drop_first=False,
        )

        # =================================================
        # FEATURE ALIGNMENT
        # =================================================
        df = df.reindex(
            columns=all_features,
            fill_value=0,
        )

        # =================================================
        # PREDICTION
        # =================================================
        prediction = model.predict(df)

        predicted_consumption = float(
            np.expm1(prediction[0])
        )

        # =================================================
        # OPTIONAL BILL PREDICTION
        # =================================================
        estimated_bill = (
            predicted_consumption * 8
        )

        # =================================================
        # RESPONSE
        # =================================================
        return {

            "resource_type": resource_type,

            "user_id": str(user_id),

            "month": month,

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

    except Exception as e:

        raise Exception(
            f"Prediction failed for "
            f"{resource_type}: {str(e)}"
        )
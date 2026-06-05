# Machine_Learning/predict.py

import json
import pandas as pd
import numpy as np

from Machine_Learning.preprocessing import (
    preprocess_dataframe,
)

from Machine_Learning.feature_engineering import (
    create_features,
)

from Machine_Learning.model_loader import (
    load_model_artifacts,
)

from Machine_Learning.constants import (
    BILL_RULES,
    USAGE_THRESHOLDS,
)


# =========================================================
# BILL ENGINE
# =========================================================
def calculate_bill(
    resource,
    units,
):

    units = max(
        float(units),
        0,
    )

    rules = BILL_RULES.get(
        resource,
        {},
    )

    if resource == "electricity":

        if units <= rules["slab_1_limit"]:

            return (
                units
                * rules["slab_1_rate"]
            )

        elif units <= rules["slab_2_limit"]:

            return (

                rules["slab_1_limit"]
                *
                rules["slab_1_rate"]

                +

                (
                    units
                    -
                    rules["slab_1_limit"]
                )

                *

                rules["slab_2_rate"]
            )

        return (

            rules["slab_1_limit"]
            *
            rules["slab_1_rate"]

            +

            (
                rules["slab_2_limit"]
                -
                rules["slab_1_limit"]
            )

            *

            rules["slab_2_rate"]

            +

            (
                units
                -
                rules["slab_2_limit"]
            )

            *

            rules["slab_3_rate"]
        )

    if "rate" in rules:

        return (
            units
            *
            rules["rate"]
        )

    return 0


# =========================================================
# FEATURE PIPELINE
# =========================================================
def build_features(
    df,
):

    df = preprocess_dataframe(
        df
    )

    df = create_features(
        df
    )

    return df


# =========================================================
# USAGE LABEL
# =========================================================
def get_usage_level(
    value,
):

    if value < USAGE_THRESHOLDS["low"]:

        return "Low"

    elif value < USAGE_THRESHOLDS["moderate"]:

        return "Moderate"

    return "High"


# =========================================================
# PREDICTION
# =========================================================
def predict_consumption(
    resource,
    input_data,
):

    resource = (
        resource
        .strip()
        .lower()
    )

    artifacts = (
        load_model_artifacts(
            resource
        )
    )

    model = artifacts[
        "model"
    ]

    feature_names = artifacts[
        "feature_names"
    ]

    # ---------------------
    # INPUT
    # ---------------------
    df = pd.DataFrame(
        [
            input_data
        ]
    )

    # ---------------------
    # EXACT TRAIN PIPELINE
    # ---------------------
    df = build_features(
        df
    )

    # ---------------------
    # STRICT ALIGNMENT
    # ---------------------
    df = (
        df
        .reindex(
            columns=feature_names,
            fill_value=0,
        )
    )

    # ---------------------
    # PREDICT
    # ---------------------
    pred_log = (
        model.predict(
            df
        )[0]
    )

    prediction = (
        float(
            max(
                np.expm1(
                    pred_log
                ),
                0,
            )
        )
    )

    bill = (
        calculate_bill(
            resource,
            prediction,
        )
    )

    return {

        "resource":
            resource,

        "predicted_consumption":
            round(
                prediction,
                2,
            ),

        "estimated_bill":
            round(
                bill,
                2,
            ),

        "usage_level":
            get_usage_level(
                prediction
            ),
    }


# =========================================================
# TEST
# =========================================================
if __name__ == "__main__":

    sample = {
        "num_people": 8,
        "bedrooms": 5,
        "has_ac": True,
        "vacation_days": 0,
        "month": "June",
        "climate": "hot",
    }

    result = (
        predict_consumption(
            "electricity",
            sample,
        )
    )

    print(
        json.dumps(
            result,
            indent=4,
        )
    )
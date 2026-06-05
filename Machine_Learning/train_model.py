# Machine_Learning/train_model.py

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

from xgboost import XGBRegressor
from sklearn.model_selection import (
    train_test_split,
    cross_val_score,
)

# =========================================================
# PATH SETUP
# =========================================================
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
        )
    )
)

from Machine_Learning.preprocessing import (
    preprocess_dataframe,
)

from Machine_Learning.feature_engineering import (
    create_features,
)

from Machine_Learning.evaluation import (
    evaluate_model,
)

from Machine_Learning.constants import (
    get_resource_config,
    TEST_SIZE,
    RANDOM_STATE,
    XGBOOST_PARAMS,
)

# =========================================================
# RESOURCE
# =========================================================
RESOURCE = "electricity"   

CONFIG = get_resource_config(
    RESOURCE
)

DATASET_PATH = CONFIG[
    "dataset_path"
]

TARGET_COLUMN = CONFIG[
    "target_column"
]

MODEL_PATH = CONFIG[
    "model_path"
]

FEATURES_PATH = CONFIG[
    "features_path"
]

np.random.seed(
    RANDOM_STATE
)


# =========================================================
# LOAD DATA
# =========================================================
def load_dataset():

    if not os.path.exists(
        DATASET_PATH
    ):

        raise FileNotFoundError(
            f"Dataset not found:\n{DATASET_PATH}"
        )

    df = pd.read_csv(
        DATASET_PATH
    )

    if TARGET_COLUMN not in df.columns:

        raise ValueError(
            f"{TARGET_COLUMN} missing"
        )

    print(
        f"\nDataset Loaded: {df.shape}"
    )

    return df


# =========================================================
# REMOVE OUTLIERS
# =========================================================
def remove_outliers_train_only(
    df
):

    df = df.copy()

    low = (
        df[
            TARGET_COLUMN
        ]
        .quantile(
            0.01
        )
    )

    high = (
        df[
            TARGET_COLUMN
        ]
        .quantile(
            0.99
        )
    )

    return df[
        (
            df[
                TARGET_COLUMN
            ] >= low
        )
        &
        (
            df[
                TARGET_COLUMN
            ] <= high
        )
    ]


# =========================================================
# SHARED PIPELINE
# =========================================================
def build_features(
    df
):

    df = preprocess_dataframe(
        df
    )

    df = create_features(
        df
    )

    return df


# =========================================================
# PREP DATA
# =========================================================
def prepare_data(
    df
):

    train_df, test_df = (
        train_test_split(

            df,

            test_size=TEST_SIZE,

            random_state=RANDOM_STATE,
        )
    )

    train_df = (
        remove_outliers_train_only(
            train_df
        )
    )

    train_df = (
        build_features(
            train_df
        )
    )

    test_df = (
        build_features(
            test_df
        )
    )

    y_train = np.log1p(
        train_df[
            TARGET_COLUMN
        ]
    )

    y_test = np.log1p(
        test_df[
            TARGET_COLUMN
        ]
    )

    X_train = train_df.drop(
        columns=[
            TARGET_COLUMN
        ]
    )

    X_test = test_df.drop(
        columns=[
            TARGET_COLUMN
        ]
    )

    X_train = pd.get_dummies(
        X_train
    )

    X_test = pd.get_dummies(
        X_test
    )

    X_test = (
        X_test
        .reindex(
            columns=X_train.columns,
            fill_value=0,
        )
    )

    os.makedirs(
        os.path.dirname(
            FEATURES_PATH
        ),
        exist_ok=True,
    )

    with open(
        FEATURES_PATH,
        "w",
    ) as f:

        json.dump(
            {
                "resource":
                    RESOURCE,

                "features":
                    list(
                        X_train.columns
                    ),
            },
            f,
            indent=4,
        )

    return (
        X_train,
        X_test,
        y_train,
        y_test,
    )


# =========================================================
# MODEL
# =========================================================
def build_model():

    return XGBRegressor(
        **XGBOOST_PARAMS
    )


# =========================================================
# TRAIN
# =========================================================
def train_model():

    df = load_dataset()

    (
        X_train,
        X_test,
        y_train,
        y_test,
    ) = prepare_data(
        df
    )

    model = (
        build_model()
    )

    print(
        "\nTraining..."
    )

    model.fit(
        X_train,
        y_train,
    )

    preds = np.expm1(
        model.predict(
            X_test
        )
    )

    y_true = np.expm1(
        y_test
    )

    metrics = (
        evaluate_model(
            y_true,
            preds,
        )
    )

    train_r2 = (
        model.score(
            X_train,
            y_train,
        )
    )

    test_r2 = (
        model.score(
            X_test,
            y_test,
        )
    )

    cv = (
        cross_val_score(
            model,
            X_train,
            y_train,
            cv=5,
            scoring="r2",
            n_jobs=-1,
        )
    )

    os.makedirs(
        os.path.dirname(
            MODEL_PATH
        ),
        exist_ok=True,
    )

    joblib.dump(
        model,
        MODEL_PATH,
    )

    print(
        f"\nSaved:\n{MODEL_PATH}"
    )

    return {

        "resource":
            RESOURCE,

        "metrics":
            metrics,

        "train_r2":
            float(
                train_r2
            ),

        "test_r2":
            float(
                test_r2
            ),

        "cv_score":
            float(
                cv.mean()
            ),
    }


# =========================================================
# ENTRY
# =========================================================
if __name__ == "__main__":

    result = (
        train_model()
    )

    print(
        json.dumps(
            result,
            indent=4,
        )
    )
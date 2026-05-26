# Machine_Learning/constants.py

# =========================================================
# MODEL VERSIONING
# =========================================================
MODEL_VERSION = "v1"


# =========================================================
# BASE MODEL DIRECTORY
# =========================================================
MODEL_DIRECTORY = "Machine_Learning/model_versions"


# =========================================================
# MODEL TYPE
# =========================================================
MODEL_TYPE = "xgboost"


# =========================================================
# MAIN MODEL FILE
# =========================================================
# XGBoost model saved using joblib
# Example:
# electricity_xgboost_v1.pkl
# =========================================================
MODEL_FILE_NAME = (
    f"electricity_{MODEL_TYPE}_{MODEL_VERSION}.pkl"
)

MODEL_PATH = (
    f"{MODEL_DIRECTORY}/{MODEL_FILE_NAME}"
)


# =========================================================
# FEATURE FILE
# =========================================================
FEATURES_FILE_NAME = (
    f"features_{MODEL_VERSION}.json"
)

FEATURES_PATH = (
    f"{MODEL_DIRECTORY}/{FEATURES_FILE_NAME}"
)


# =========================================================
# TRAINING DATASET
# =========================================================
DATASET_FILE_NAME = (
    "electricity_sample_data_500_rows.csv"
)

DATASET_PATH = (
    f"Machine_Learning/datasets/{DATASET_FILE_NAME}"
)


# =========================================================
# TARGET COLUMN
# =========================================================
TARGET_COLUMN = "electricity_consumption"


# =========================================================
# TRAIN / TEST CONFIG
# =========================================================
TEST_SIZE = 0.2

RANDOM_STATE = 42


# =========================================================
# XGBOOST TRAINING PARAMETERS
# =========================================================
XGBOOST_PARAMS = {

    # -----------------------------------------------------
    # OBJECTIVE
    # -----------------------------------------------------
    "objective": "reg:squarederror",

    # -----------------------------------------------------
    # BOOSTING
    # -----------------------------------------------------
    "n_estimators": 500,

    "learning_rate": 0.03,

    "max_depth": 6,

    "min_child_weight": 3,

    # -----------------------------------------------------
    # REGULARIZATION
    # -----------------------------------------------------
    "gamma": 0.1,

    "reg_alpha": 0.1,

    "reg_lambda": 1.0,

    # -----------------------------------------------------
    # SAMPLING
    # -----------------------------------------------------
    "subsample": 0.8,

    "colsample_bytree": 0.8,

    # -----------------------------------------------------
    # PERFORMANCE
    # -----------------------------------------------------
    "random_state": RANDOM_STATE,

    "n_jobs": -1,
}


# =========================================================
# PREDICTION SETTINGS
# =========================================================
DEFAULT_BILLING_DAYS = 30

DEFAULT_CLIMATE = "moderate"

DEFAULT_MONTH = 1

DEFAULT_YEAR = 2025


# =========================================================
# ELECTRICITY BILL SLABS
# =========================================================
BILL_SLABS = {

    "slab_1_limit": 100,
    "slab_1_rate": 5,

    "slab_2_limit": 300,
    "slab_2_rate": 7,

    "slab_3_rate": 10,
}


# =========================================================
# USAGE LEVEL THRESHOLDS
# =========================================================
LOW_USAGE_THRESHOLD = 200

MODERATE_USAGE_THRESHOLD = 500


# =========================================================
# LOGGING FLAGS
# =========================================================
ENABLE_TRAINING_LOGS = True

ENABLE_PREDICTION_LOGS = True


# =========================================================
# FUTURE SUPPORT
# =========================================================
SUPPORTED_RESOURCE_TYPES = [
    "Electricity",
    "Water",
    "Gas",
    "Fuel",
]
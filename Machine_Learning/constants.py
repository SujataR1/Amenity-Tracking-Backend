import os


# =========================================================
# GLOBAL SETTINGS
# =========================================================
MODEL_VERSION = "v1"
MODEL_TYPE = "xgboost"

TEST_SIZE = 0.20
RANDOM_STATE = 42


# =========================================================
# DIRECTORIES
# =========================================================
BASE_DIR = os.path.dirname(__file__)

MODEL_DIRECTORY = os.path.join(
    BASE_DIR,
    "model_versions",
)

DATASET_DIRECTORY = os.path.join(
    BASE_DIR,
    "datasets",
)


# =========================================================
# SUPPORTED RESOURCE TYPES
# =========================================================
SUPPORTED_RESOURCE_TYPES = [
    "electricity",
    "water",
    "gas",
    "fuel",
]


# =========================================================
# RESOURCE CONFIG
# =========================================================
RESOURCE_CONFIG = {

    # -----------------------------------------------------
    # ELECTRICITY
    # -----------------------------------------------------
    "electricity": {
        "enabled": True,
        "target_column": "electricity_consumption",
        "dataset": "electricity_sample_data_500_rows.csv",
        "model": f"electricity_{MODEL_TYPE}_{MODEL_VERSION}.pkl",
        "features": f"electricity_features_{MODEL_VERSION}.json",
    },

    # -----------------------------------------------------
    # WATER
    # -----------------------------------------------------
    "water": {
        "enabled": True,
        "target_column": "total_liters",
        "dataset": "water_6_month_usage_dataset_3000.csv",
        "model": f"water_{MODEL_TYPE}_{MODEL_VERSION}.pkl",
        "features": f"water_features_{MODEL_VERSION}.json",
    },

    # -----------------------------------------------------
    # GAS (ENABLED NOW)
    # -----------------------------------------------------
    "gas": {
        "enabled": True,
        "target_column": "gas_units",
        "dataset": "gas_6_month_usage_dataset_3000.csv",
        "model": f"gas_{MODEL_TYPE}_{MODEL_VERSION}.pkl",
        "features": f"gas_features_{MODEL_VERSION}.json",
    },

    # -----------------------------------------------------
    # FUEL
    # -----------------------------------------------------
    "fuel": {
        "enabled": True,
        "target_column": "total_fuel_liters",
        "dataset": "fuel_6_month_historical_dataset_3000.csv",
        "model": f"fuel_{MODEL_TYPE}_{MODEL_VERSION}.pkl",
        "features": f"fuel_features_{MODEL_VERSION}.json",
    },
}


# =========================================================
# CONFIG RESOLVER
# =========================================================
def get_resource_config(resource_type):

    resource = str(resource_type).strip().lower()

    if resource not in RESOURCE_CONFIG:
        raise ValueError(
            f"Unsupported resource: {resource}. "
            f"Supported: {SUPPORTED_RESOURCE_TYPES}"
        )

    cfg = RESOURCE_CONFIG[resource]

    if not cfg.get("enabled", False):
        raise ValueError(
            f"{resource} training disabled"
        )

    required = [
        "target_column",
        "dataset",
        "model",
        "features",
    ]

    missing = [
        field
        for field in required
        if not cfg.get(field)
    ]

    if missing:
        raise ValueError(
            f"Incomplete RESOURCE_CONFIG "
            f"for {resource}: {missing}"
        )

    return {

        "resource":
            resource,

        "target_column":
            cfg["target_column"],

        "dataset_path":
            os.path.join(
                DATASET_DIRECTORY,
                cfg["dataset"],
            ),

        "model_path":
            os.path.join(
                MODEL_DIRECTORY,
                cfg["model"],
            ),

        "features_path":
            os.path.join(
                MODEL_DIRECTORY,
                cfg["features"],
            ),
    }


# =========================================================
# TRAIN CONFIG
# =========================================================
XGBOOST_PARAMS = {

    "objective":
        "reg:squarederror",

    "n_estimators":
        600,

    "learning_rate":
        0.03,

    "max_depth":
        5,

    "min_child_weight":
        3,

    "gamma":
        0.1,

    "reg_alpha":
        0.1,

    "reg_lambda":
        1.5,

    "subsample":
        0.8,

    "colsample_bytree":
        0.8,

    "random_state":
        RANDOM_STATE,

    "n_jobs":
        -1,
}


# =========================================================
# DEFAULTS
# =========================================================
DEFAULT_VALUES = {

    "billing_days": 30,

    "month": 1,

    "year": 2026,

    "climate": "moderate",
}


# =========================================================
# BILLING
# =========================================================
BILL_RULES = {

    "electricity": {
        "slab_1_limit": 100,
        "slab_1_rate": 5,
        "slab_2_limit": 300,
        "slab_2_rate": 7,
        "slab_3_rate": 10,
    },

    "water": {
        "rate": 0.03,
    },

    "gas": {
        "rate": 25,
    },

    "fuel": {
        "rate": 110,
    },
}


# =========================================================
# THRESHOLDS
# =========================================================
USAGE_THRESHOLDS = {

    "low": 200,

    "moderate": 500,
}


# =========================================================
# LOGGING
# =========================================================
ENABLE_TRAINING_LOGS = True
ENABLE_PREDICTION_LOGS = True
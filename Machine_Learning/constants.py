# Machine_Learning/constants.py

# =========================================================
# MODEL VERSIONING
# =========================================================
MODEL_VERSION = "v1"

# =========================================================
# BASE DIRECTORY
# =========================================================
MODEL_DIRECTORY = "Machine_Learning/model_versions"

# =========================================================
# PYTORCH MODEL FILE (IMPORTANT FIX)
# -----------------
# ❌ OLD: .pkl (sklearn joblib)
# ✅ NEW: .pt (PyTorch state_dict)
# =========================================================
MODEL_FILE_NAME = f"electricity_model_{MODEL_VERSION}.pt"
MODEL_PATH = f"{MODEL_DIRECTORY}/{MODEL_FILE_NAME}"

# =========================================================
# TRAINING CONFIG
# =========================================================
TARGET_COLUMN = "electricity_consumption"
TEST_SIZE = 0.2
RANDOM_STATE = 42

# =========================================================
# ARTIFACT PATHS (IMPORTANT FOR CONSISTENCY)
# =========================================================
SCALER_FILE_NAME = f"scaler_{MODEL_VERSION}.pkl"
FEATURES_FILE_NAME = f"features_{MODEL_VERSION}.json"
USER_MAP_FILE_NAME = f"user_map_{MODEL_VERSION}.pkl"

SCALER_PATH = f"{MODEL_DIRECTORY}/{SCALER_FILE_NAME}"
FEATURES_PATH = f"{MODEL_DIRECTORY}/{FEATURES_FILE_NAME}"
USER_MAP_PATH = f"{MODEL_DIRECTORY}/{USER_MAP_FILE_NAME}"
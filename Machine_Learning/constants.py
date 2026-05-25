# Machine_Learning/constants.py

MODEL_VERSION = "v1"

MODEL_DIRECTORY = "Machine_Learning/model_versions"

MODEL_FILE_NAME = f"electricity_model_{MODEL_VERSION}.pkl"

MODEL_PATH = f"{MODEL_DIRECTORY}/{MODEL_FILE_NAME}"

TARGET_COLUMN = "electricity_consumption"

TEST_SIZE = 0.2

RANDOM_STATE = 42
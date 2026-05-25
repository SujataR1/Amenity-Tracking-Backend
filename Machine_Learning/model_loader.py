# Machine_Learning/model_loader.py

import joblib
from Machine_Learning.constants import MODEL_PATH


def load_model():

    model = joblib.load(MODEL_PATH)

    return model
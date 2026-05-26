# Machine_Learning/model_loader.py

import torch
from Machine_Learning.Methods import ConsumptionModel
from Machine_Learning.constants import MODEL_PATH
import pickle


# =========================================================
# LOAD USER MAPPING (IMPORTANT FOR EMBEDDING)
# =========================================================
def load_user_map():
    try:
        with open("Machine_Learning/model_versions/user_map.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None


# =========================================================
# LOAD PYTORCH MODEL
# =========================================================
def load_model(input_dim=None):

    user_map = load_user_map()
    num_users = len(user_map) if user_map else 1

    # -----------------------------
    # CREATE MODEL STRUCTURE
    # -----------------------------
    model = ConsumptionModel(
        num_users=num_users,
        input_dim=input_dim if input_dim else 10,  # fallback safety
        hidden_dim1=128,
        hidden_dim2=64,
        embedding_dim=32,
        dropout_rate=0.2
    )

    # -----------------------------
    # LOAD STATE DICT
    # -----------------------------
    model.load_state_dict(
        torch.load(MODEL_PATH, map_location=torch.device("cpu"))
    )

    model.eval()

    return model
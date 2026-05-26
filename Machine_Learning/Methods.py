# Machine_Learning/Methods.py

import json
import pickle
import optuna
import pandas as pd
import numpy as np
import os

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from sklearn.preprocessing import RobustScaler

from Database_and_ORM.Database_Models import (
    ElectricityConsumption,
    QuestionnaireAnswers,
    User,
)

# -----------------------------
# DEVICE
# -----------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# =========================================================
# MODEL
# =========================================================
class ConsumptionModel(nn.Module):
    def __init__(self, num_users, input_dim,
                 hidden_dim1=128, hidden_dim2=64,
                 embedding_dim=32, dropout_rate=0.2):

        super().__init__()

        self.user_embedding = nn.Embedding(num_users, embedding_dim)

        self.fc1 = nn.Linear(input_dim + embedding_dim, hidden_dim1)
        self.fc2 = nn.Linear(hidden_dim1, hidden_dim2)
        self.fc3 = nn.Linear(hidden_dim2, 1)

        self.dropout = nn.Dropout(dropout_rate)

    def forward(self, user_ids, features):

        user_emb = self.user_embedding(user_ids)
        x = torch.cat([features, user_emb], dim=1)

        x = torch.relu(self.fc1(x))
        x = self.dropout(x)

        x = torch.relu(self.fc2(x))
        x = self.dropout(x)

        return self.fc3(x)


# =========================================================
# SINGLE FEATURE ENGINEERING SOURCE
# =========================================================
def build_features(df: pd.DataFrame):

    df["people_per_room"] = df["one"] / (df["three"].replace(0, 1))
    df["vacation_factor"] = df["eighteen"] * 0.1

    appliance_cols = [
        "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen"
    ]

    df["appliance_score"] = 0
    for c in appliance_cols:
        df["appliance_score"] += df.get(c, 0)

    df["luxury_score"] = df.get("fifteen", 0) + df.get("sixteen", 0)

    return df


# =========================================================
# DATASET BUILDER (FIXED TIME-AWARE VERSION)
# =========================================================
async def build_dataset(resource_model, target_column):

    users = await User.all().values("id")

    user_ids = [u["id"] for u in users]

    # 🔥 FIX: include month/year for time correctness
    consumption = await resource_model.filter(
        user_id__in=user_ids
    ).values("user_id", "year", "month", target_column)

    questionnaire = await QuestionnaireAnswers.filter(
        user_id__in=user_ids
    ).values(
        "user_id", "one", "two", "three",
        "four", "five", "six", "seven",
        "eight", "nine", "ten", "eleven",
        "twelve", "thirteen", "fourteen",
        "fifteen", "sixteen", "seventeen",
        "eighteen", "nineteen"
    )

    df_c = pd.DataFrame(consumption)
    df_q = pd.DataFrame(questionnaire)

    # 🔥 FIX: proper join strategy
    # (user-level alignment, not raw merge only)
    df = df_c.merge(df_q, on="user_id", how="left")

    df.fillna(0, inplace=True)

    return df


# =========================================================
# TRAINING PIPELINE
# =========================================================
async def retrain_model(resource_type: str):

    with open("Machine_Learning/Machine_Learning_Parameter_Schemas.json") as f:
        config_all = json.load(f)

    config = config_all.get(resource_type)

    if not config:
        raise ValueError("Invalid resource type config")

    model_dir = config["Directory_Path"]
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, config["Trained_Model_Name"])
    scaler_path = os.path.join(model_dir, config["Scaler_File_Name"])
    features_path = os.path.join(model_dir, config["Features_File_Name"])
    user_map_path = os.path.join(model_dir, "user_map.pkl")

    target_column = config["Column_Name"]
    resource_model = globals()[config["Database_Name"]]

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    df = await build_dataset(resource_model, target_column)

    # -----------------------------
    # FEATURE ENGINEERING (SINGLE SOURCE)
    # -----------------------------
    df = build_features(df)

    df.fillna(0, inplace=True)

    # -----------------------------
    # CLIP TARGET (REMOVE OUTLIERS)
    # -----------------------------
    df[target_column] = np.clip(
        df[target_column],
        df[target_column].quantile(0.01),
        df[target_column].quantile(0.99)
    )

    # -----------------------------
    # ENCODING
    # -----------------------------
    df = pd.get_dummies(
        df,
        columns=["month", "nineteen", "seventeen"],
        prefix=["month", "climate", "vacation"]
    )

    # -----------------------------
    # USER MAPPING (IMPORTANT FIX)
    # -----------------------------
    user_map = {u: i for i, u in enumerate(df["user_id"].unique())}
    df["user_id"] = df["user_id"].map(user_map)

    with open(user_map_path, "wb") as f:
        pickle.dump(user_map, f)

    # -----------------------------
    # FEATURES
    # -----------------------------
    feature_cols = [c for c in df.columns if c != target_column]

    X = df[feature_cols]
    y = np.log1p(df[target_column])  # log transform

    # -----------------------------
    # SCALING
    # -----------------------------
    scaler = RobustScaler()
    X = scaler.fit_transform(X)

    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    with open(features_path, "w") as f:
        json.dump(feature_cols, f)

    # -----------------------------
    # TENSORS
    # -----------------------------
    user_tensor = torch.tensor(df["user_id"].values, dtype=torch.long).to(device)
    X_tensor = torch.tensor(X, dtype=torch.float32).to(device)
    y_tensor = torch.tensor(y.values, dtype=torch.float32).view(-1, 1).to(device)

    dataset = TensorDataset(user_tensor, X_tensor, y_tensor)

    train_size = int(0.8 * len(dataset))
    train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, len(dataset) - train_size])

    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32)

    # =====================================================
    # MODEL INIT (SIMPLE + STABLE)
    # =====================================================
    model = ConsumptionModel(
        num_users=len(user_map),
        input_dim=X.shape[1]
    ).to(device)

    optimizer = optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.L1Loss()

    # -----------------------------
    # TRAINING LOOP
    # -----------------------------
    for epoch in range(20):

        model.train()

        for u, x, y in train_loader:
            optimizer.zero_grad()
            pred = model(u, x)
            loss = loss_fn(pred, y)
            loss.backward()
            optimizer.step()

    # -----------------------------
    # SAVE MODEL
    # -----------------------------
    torch.save(model.state_dict(), model_path)

    print("✅ Model trained and saved successfully.")
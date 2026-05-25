# Machine_Learning/Methods.py

import json
import pickle
import optuna
import pandas as pd
import numpy as np
import os
from time import time
from datetime import datetime
from os import path, makedirs

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
    def __init__(self, num_users, input_dim, hidden_dim1, hidden_dim2,
                 embedding_dim=50, dropout_rate=0.2):

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
# FEATURE BUILDER (SINGLE SOURCE OF TRUTH)
# =========================================================
def build_features(df: pd.DataFrame):

    df["people_per_room"] = df["one"] / (df["three"] + 1)
    df["vacation_factor"] = df["eighteen"] * 0.1

    df["appliance_score"] = (
        df["four"] + df["five"] + df["six"] + df["seven"] +
        df["eight"] + df["nine"] + df["ten"] +
        df["eleven"] + df["twelve"] + df["thirteen"]
    )

    df["luxury_score"] = df["fifteen"] + df["sixteen"]

    return df


# =========================================================
# DATASET BUILDER (IMPORTANT FIX)
# =========================================================
async def build_dataset(resource_model, target_column):

    users = await User.all().values("id", "pin_code")

    user_ids = [u["id"] for u in users]

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

    df1 = pd.DataFrame(consumption)
    df2 = pd.DataFrame(questionnaire)

    df = df1.merge(df2, on="user_id", how="left")
    df.fillna(0, inplace=True)

    return df


# =========================================================
# TRAINING PIPELINE
# =========================================================
async def retrain_model(resource_type: str):

    with open(
        "Machine_Learning/Machine_Learning_Parameter_Schemas.json"
    ) as f:
        config_all = json.load(f)

    config = config_all.get(resource_type)

    if not config:
        raise ValueError("Invalid resource type config")

    model_dir = config["Directory_Path"]
    os.makedirs(model_dir, exist_ok=True)

    model_path = path.join(model_dir, config["Trained_Model_Name"])
    scaler_path = path.join(model_dir, config["Scaler_File_Name"])
    features_path = path.join(model_dir, config["Features_File_Name"])

    target_column = config["Column_Name"]
    resource_model = globals()[config["Database_Name"]]

    # -----------------------------
    # LOAD DATA ONCE (FIXED)
    # -----------------------------
    df = await build_dataset(resource_model, target_column)

    # -----------------------------
    # FEATURE ENGINEERING
    # -----------------------------
    df = build_features(df)

    # -----------------------------
    # CLEAN DATA
    # -----------------------------
    df.fillna(0, inplace=True)

    df[target_column] = np.clip(
        df[target_column],
        df[target_column].quantile(0.01),
        df[target_column].quantile(0.99)
    )

    # -----------------------------
    # ENCODING (CONSISTENT)
    # -----------------------------
    df = pd.get_dummies(
        df,
        columns=["month", "nineteen", "seventeen"],
        prefix=["month", "climate", "vacation"]
    )

    # -----------------------------
    # USER MAPPING (embedding fix)
    # -----------------------------
    user_map = {
        u: i for i, u in enumerate(df["user_id"].unique())
    }
    df["user_id"] = df["user_id"].map(user_map)

    # -----------------------------
    # FEATURES
    # -----------------------------
    feature_cols = [c for c in df.columns if c != target_column]

    X = df[feature_cols]
    y = np.log1p(df[target_column])

    # -----------------------------
    # SCALE
    # -----------------------------
    scaler = RobustScaler()
    X = scaler.fit_transform(X)

    # save artifacts
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    with open(features_path, "w") as f:
        json.dump(feature_cols, f)

    # -----------------------------
    # TENSOR DATA
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
    # OPTUNA OBJECTIVE
    # =====================================================
    def objective(trial):

        model = ConsumptionModel(
            num_users=len(user_map),
            input_dim=X.shape[1],
            hidden_dim1=trial.suggest_int("h1", 64, 256),
            hidden_dim2=trial.suggest_int("h2", 32, 128),
            embedding_dim=trial.suggest_int("emb", 10, 64),
            dropout_rate=trial.suggest_float("dropout", 0.1, 0.5)
        ).to(device)

        optimizer = optim.Adam(model.parameters(),
                                lr=trial.suggest_float("lr", 1e-4, 1e-2, log=True))

        loss_fn = nn.L1Loss()

        for _ in range(10):  # simplified training per trial
            model.train()
            for u, x, y in train_loader:
                optimizer.zero_grad()
                pred = model(u, x)
                loss = loss_fn(pred, y)
                loss.backward()
                optimizer.step()

        model.eval()
        errors = []

        with torch.no_grad():
            for u, x, y in val_loader:
                pred = model(u, x)
                errors.append(torch.abs(pred - y).mean().item())

        return np.mean(errors)


    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=10)

    best = study.best_params

    # =====================================================
    # FINAL MODEL
    # =====================================================
    model = ConsumptionModel(
        num_users=len(user_map),
        input_dim=X.shape[1],
        hidden_dim1=best["h1"],
        hidden_dim2=best["h2"],
        embedding_dim=best["emb"],
        dropout_rate=best["dropout"]
    ).to(device)

    optimizer = optim.Adam(model.parameters(), lr=best["lr"])
    loss_fn = nn.L1Loss()

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

    print("Training complete and model saved.")
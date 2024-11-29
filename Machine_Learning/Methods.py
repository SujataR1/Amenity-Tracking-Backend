import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import make_scorer
from tortoise.transactions import in_transaction
from tortoise.functions import Avg
from datetime import datetime
from Database_and_ORM.Database_Models import (
    ElectricityConsumption,
    QuestionnaireAnswers,
    User,
)
import json
from decouple import config
from os import path, makedirs
from time import time
from sklearn.preprocessing import RobustScaler
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import optuna


class ElectricityConsumptionModel(nn.Module):
    def __init__(self, input_dim, hidden_dim1, hidden_dim2):
        super(ElectricityConsumptionModel, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim1),
            nn.ReLU(),
            nn.Linear(hidden_dim1, hidden_dim2),
            nn.ReLU(),
            nn.Linear(hidden_dim2, 1),
        )

    def forward(self, x):
        return self.net(x)


async def retrain_model():
    """
    Retrains the electricity consumption prediction model using PyTorch
    and Optuna for hyperparameter tuning. Saves state after each fitting attempt.
    """
    model_dir = config("ELECTRICITY_CONSUMPTION_MODEL_PATH")
    model_path = path.join(model_dir, "Electricity_Consumption_Model.pt")
    status_json_path = path.join(
        model_dir, "Electricity_Consumption_Model_Update_Status.json"
    )
    features_path = path.join(
        model_dir, "Electricity_Consumption_Model_Features.json"
    )
    hyperparam_config_path = path.join(model_dir, "ML_Config.json")

    if not path.exists(model_dir):
        makedirs(model_dir, exist_ok=True)

    start_time = time()
    max_duration = 7 * 3600  # 7 hours for training
    mae = float("inf")
    iteration = 0

    try:
        while mae > 3 and (time() - start_time) < max_duration:
            iteration += 1
            print(f"Retraining iteration {iteration}...")

            # Fetch data in batches
            offset = 0
            batch_size = 25
            merged_data = []

            while True:
                users_batch = (
                    await User.all()
                    .offset(offset)
                    .limit(batch_size)
                    .values("id", "pin_code")
                )
                if not users_batch:
                    break

                user_ids = [user["id"] for user in users_batch]
                consumption_batch = await ElectricityConsumption.filter(
                    user_id__in=user_ids
                ).values("user_id", "year", "month", "electricity_consumption")
                questionnaire_batch = await QuestionnaireAnswers.filter(
                    user_id__in=user_ids
                ).values(
                    "user_id",
                    "one",
                    "two",
                    "three",
                    "four",
                    "five",
                    "six",
                    "seven",
                    "eight",
                    "nine",
                    "ten",
                    "eleven",
                    "twelve",
                    "thirteen",
                    "fourteen",
                    "fifteen",
                    "sixteen",
                    "seventeen",
                    "eighteen",
                    "nineteen",
                )

                # Add pin_code to each user's data from the related User model
                for consumption in consumption_batch:
                    user_id = consumption["user_id"]
                    user_entry = next(
                        (
                            user
                            for user in users_batch
                            if user["id"] == user_id
                        ),
                        None,
                    )
                    if user_entry:
                        consumption["pin_code"] = user_entry["pin_code"]

                batch_data = pd.merge(
                    pd.DataFrame(consumption_batch),
                    pd.DataFrame(questionnaire_batch),
                    on="user_id",
                    how="left",
                )
                merged_data.append(batch_data)
                offset += batch_size

            if merged_data:
                final_data = pd.concat(merged_data, ignore_index=True)
            else:
                raise ValueError("No data available for training.")

            print(f"Final data shape: {final_data.shape}")

            # Process features for model input
            processed_data = final_data.copy()
            if processed_data.empty:
                raise ValueError(
                    "Processed data is empty after feature engineering."
                )

            # Encode categorical features: month, nineteen (climate), and seventeen (vacation months)
            processed_data = pd.get_dummies(
                processed_data,
                columns=["month", "nineteen", "seventeen"],
                prefix=["month", "climate", "vacation_month"],
            )

            # Define feature columns
            feature_names = [
                "year",
                "pin_code",
                "one",
                "two",
                "three",
                "four",
                "five",
                "six",
                "seven",
                "eight",
                "nine",
                "ten",
                "eleven",
                "twelve",
                "thirteen",
                "fourteen",
                "fifteen",
                "sixteen",
                "eighteen",
            ] + [
                col
                for col in processed_data.columns
                if col.startswith("month_")
                or col.startswith("climate_")
                or col.startswith("vacation_month_")
            ]

            X = processed_data[feature_names]
            y = processed_data["electricity_consumption"]

            print(f"Target variable (y) shape: {y.shape}")

            # Log transform the target variable
            y = np.log1p(y)

            # Scale features
            scaler = RobustScaler()
            X_scaled = scaler.fit_transform(X)

            # Convert data to PyTorch tensors
            X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
            y_tensor = torch.tensor(y.values, dtype=torch.float32).view(-1, 1)

            dataset = TensorDataset(X_tensor, y_tensor)
            train_size = int(0.8 * len(dataset))
            val_size = len(dataset) - train_size
            train_dataset, val_dataset = torch.utils.data.random_split(
                dataset, [train_size, val_size]
            )

            train_loader = DataLoader(
                train_dataset, batch_size=32, shuffle=True
            )
            val_loader = DataLoader(val_dataset, batch_size=32)

            # Check for existing hyperparameters
            if path.exists(hyperparam_config_path):
                print(f"Loading hyperparameters from {hyperparam_config_path}")
                with open(hyperparam_config_path, "r") as config_file:
                    best_params = json.load(config_file)
            else:
                print("No saved hyperparameters found. Running Optuna...")

                def objective(trial):
                    learning_rate = trial.suggest_float(
                        "learning_rate", 1e-4, 1e-2, log=True
                    )
                    hidden_dim1 = trial.suggest_int(
                        "hidden_dim1", 64, 256, step=32
                    )
                    hidden_dim2 = trial.suggest_int(
                        "hidden_dim2", 32, 128, step=16
                    )
                    batch_size = trial.suggest_categorical(
                        "batch_size", [16, 32, 64]
                    )
                    epochs = trial.suggest_int("epochs", 10, 50)

                    train_loader = DataLoader(
                        train_dataset, batch_size=batch_size, shuffle=True
                    )
                    val_loader = DataLoader(val_dataset, batch_size=batch_size)

                    model = ElectricityConsumptionModel(
                        input_dim=len(feature_names),
                        hidden_dim1=hidden_dim1,
                        hidden_dim2=hidden_dim2,
                    )
                    device = torch.device(
                        "cuda" if torch.cuda.is_available() else "cpu"
                    )
                    model.to(device)
                    optimizer = optim.Adam(
                        model.parameters(), lr=learning_rate
                    )
                    criterion = nn.L1Loss()

                    for epoch in range(epochs):
                        model.train()
                        for batch_X, batch_y in train_loader:
                            batch_X, batch_y = batch_X.to(device), batch_y.to(
                                device
                            )
                            optimizer.zero_grad()
                            outputs = model(batch_X)
                            loss = criterion(outputs, batch_y)
                            loss.backward()
                            optimizer.step()

                    val_loss = 0.0
                    with torch.no_grad():
                        for batch_X, batch_y in val_loader:
                            batch_X, batch_y = batch_X.to(device), batch_y.to(
                                device
                            )
                            outputs = model(batch_X)
                            val_loss += criterion(outputs, batch_y).item()

                    return val_loss / len(val_loader)

                study = optuna.create_study(direction="minimize")
                study.optimize(objective, n_trials=100)
                best_params = study.best_params

                with open(hyperparam_config_path, "w") as config_file:
                    json.dump(best_params, config_file, indent=4)

            # Train final model
            final_model = ElectricityConsumptionModel(
                input_dim=len(feature_names),
                hidden_dim1=best_params["hidden_dim1"],
                hidden_dim2=best_params["hidden_dim2"],
            )
            device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )
            final_model.to(device)
            optimizer = optim.Adam(
                final_model.parameters(), lr=best_params["learning_rate"]
            )
            criterion = nn.L1Loss()

            for epoch in range(best_params["epochs"]):
                final_model.train()
                for batch_X, batch_y in train_loader:
                    batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                    optimizer.zero_grad()
                    outputs = final_model(batch_X)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()

            torch.save(final_model.state_dict(), model_path)

            with open(features_path, "w") as features_file:
                json.dump(feature_names, features_file, indent=4)

            y_train_pred = []
            y_val_pred = []
            with torch.no_grad():
                for batch_X, _ in train_loader:
                    y_train_pred.extend(
                        final_model(batch_X.to(device)).cpu().numpy()
                    )
                for batch_X, _ in val_loader:
                    y_val_pred.extend(
                        final_model(batch_X.to(device)).cpu().numpy()
                    )

            train_mae = mean_absolute_error(
                np.expm1(y[:train_size]), np.expm1(y_train_pred)
            )
            val_mae = mean_absolute_error(
                np.expm1(y[train_size:]), np.expm1(y_val_pred)
            )
            mae = train_mae

            training_status = {
                "iteration": iteration,
                "train_mae": train_mae,
                "val_mae": val_mae,
                "last_updated": datetime.now().isoformat(),
                "best_params": best_params,
            }
            with open(status_json_path, "w") as status_file:
                json.dump(training_status, status_file, indent=4)

            if mae <= 3:
                print("Model achieved target MAE. Training complete.")
                break

    except Exception as e:
        print(f"Error during training: {str(e)}")

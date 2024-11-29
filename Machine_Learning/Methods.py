import os
import json
import pickle
import optuna
import pandas as pd
import numpy as np
from time import time
from datetime import datetime
from os import path, makedirs
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import mean_absolute_error
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from torch.backends import cudnn
from tortoise.transactions import in_transaction
from tortoise.functions import Avg
from Database_and_ORM.Database_Models import (
    ElectricityConsumption,
    QuestionnaireAnswers,
    User,
)
from decouple import config

cudnn.benchmark = True  # Optimize GPU kernel selection for CUDA


class ElectricityConsumptionModel(nn.Module):
    def __init__(self, input_dim, hidden_dim1, hidden_dim2, dropout_rate):
        super(ElectricityConsumptionModel, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim1),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim1, hidden_dim2),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim2, 1),
        )

    def forward(self, x):
        return self.net(x)


async def retrain_model():
    """
    Retrains the electricity consumption prediction model using PyTorch
    and Optuna for hyperparameter tuning. Includes robust error handling,
    logging, versioned model saving, and resource management.
    """

    # Paths for model, scaler, and metadata
    model_dir = config("ELECTRICITY_CONSUMPTION_MODEL_PATH")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = path.join(
        model_dir, f"Electricity_Consumption_Model_{timestamp}.pt"
    )
    scaler_path = path.join(model_dir, f"Scaler_{timestamp}.pkl")
    features_path = path.join(
        model_dir, f"Electricity_Consumption_Model_Features_{timestamp}.json"
    )
    status_json_path = path.join(
        model_dir, f"Electricity_Consumption_Status_{timestamp}.json"
    )
    hyperparam_config_path = path.join(
        model_dir, f"ML_Config_{timestamp}.json"
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if not path.exists(model_dir):
        makedirs(model_dir, exist_ok=True)

    # Timer and MAE thresholds
    start_time = time()
    max_duration = 7 * 3600  # 7 hours
    mae = float("inf")
    iteration = 0

    # Ensure GPU memory usage is limited
    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(0.75, 0)

    try:
        while mae > 2 and (time() - start_time) < max_duration:
            iteration += 1
            print(f"Retraining iteration {iteration}...")

            # Fetch and preprocess data
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

                # Add pin_code to each user's data
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

            # Handle missing data
            final_data.fillna(0, inplace=True)
            print(f"Final data shape: {final_data.shape}")

            # Encode categorical features
            final_data = pd.get_dummies(
                final_data,
                columns=["month", "nineteen", "seventeen"],
                prefix=["month", "climate", "vacation_month"],
            )

            # Define features and target
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
                for col in final_data.columns
                if col.startswith("month_")
                or col.startswith("climate_")
                or col.startswith("vacation_month_")
            ]

            X = final_data[feature_names]
            y = final_data["electricity_consumption"]

            # Align features
            if path.exists(features_path):
                with open(features_path, "r") as f:
                    all_features = json.load(f)
                X = X.reindex(columns=all_features, fill_value=0)
            else:
                with open(features_path, "w") as f:
                    json.dump(feature_names, f, indent=4)

            # Log transform target variable
            y = np.log1p(y)

            # Scale features
            scaler = RobustScaler()
            X_scaled = scaler.fit_transform(X)

            # Save scaler for inference
            with open(scaler_path, "wb") as f:
                pickle.dump(scaler, f)

            # Convert to PyTorch tensors
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

            # Optuna hyperparameter optimization
            def objective(trial):
                learning_rate = trial.suggest_float(
                    "learning_rate", 1e-5, 1e-2, log=True
                )
                hidden_dim1 = trial.suggest_int(
                    "hidden_dim1", 64, 512, step=32
                )
                hidden_dim2 = trial.suggest_int(
                    "hidden_dim2", 32, 256, step=16
                )
                dropout_rate = trial.suggest_float(
                    "dropout_rate", 0.1, 0.5, step=0.1
                )
                weight_decay = trial.suggest_float(
                    "weight_decay", 1e-6, 1e-3, log=True
                )

                model = ElectricityConsumptionModel(
                    input_dim=len(feature_names),
                    hidden_dim1=hidden_dim1,
                    hidden_dim2=hidden_dim2,
                    dropout_rate=dropout_rate,
                )
                optimizer = optim.Adam(
                    model.parameters(),
                    lr=learning_rate,
                    weight_decay=weight_decay,
                )
                criterion = nn.L1Loss()
                model.to(device)

                for epoch in range(20):  # Limit epochs for faster trials
                    model.train()
                    train_loss = 0.0
                    for batch_X, batch_y in train_loader:
                        batch_X, batch_y = batch_X.to(device), batch_y.to(
                            device
                        )
                        optimizer.zero_grad()
                        outputs = model(batch_X)
                        loss = criterion(outputs, batch_y)
                        loss.backward()
                        optimizer.step()
                        train_loss += loss.item()

                    val_loss = 0.0
                    correct_predictions = 0
                    total_predictions = 0
                    with torch.no_grad():
                        model.eval()
                        for batch_X, batch_y in val_loader:
                            batch_X, batch_y = batch_X.to(device), batch_y.to(
                                device
                            )
                            outputs = model(batch_X)
                            loss = criterion(outputs, batch_y)
                            val_loss += loss.item()

                            # Error analysis
                            error = torch.abs(outputs - batch_y)
                            within_range = (
                                error <= 2
                            )  # Predictions within 2 units
                            correct_predictions += within_range.sum().item()
                            total_predictions += len(batch_y)

                    val_accuracy = (
                        correct_predictions / total_predictions
                    ) * 100
                    train_mae = train_loss / len(train_loader)
                    val_mae = val_loss / len(val_loader)
                    mae_difference = abs(train_mae - val_mae)

                    print(
                        f"Trial {trial.number} - Epoch {epoch + 1}: "
                        f"Train Loss = {train_loss:.4f}, "
                        f"Validation Loss = {val_loss:.4f}, "
                        f"Validation Accuracy = {val_accuracy:.2f}%, "
                        f"MAE Difference = {mae_difference:.4f}"
                    )

                return val_loss / len(val_loader)

            # Run Optuna optimization
            study = optuna.create_study(direction="minimize")
            study.optimize(objective, n_trials=50)
            best_params = study.best_params

            # Save hyperparameters
            with open(hyperparam_config_path, "w") as f:
                json.dump(best_params, f, indent=4)

            # Train the final model
            final_model = ElectricityConsumptionModel(
                input_dim=len(feature_names),
                hidden_dim1=best_params["hidden_dim1"],
                hidden_dim2=best_params["hidden_dim2"],
                dropout_rate=best_params["dropout_rate"],
            )
            optimizer = optim.Adam(
                final_model.parameters(),
                lr=best_params["learning_rate"],
                weight_decay=best_params["weight_decay"],
            )
            criterion = nn.L1Loss()
            final_model.to(device)

            for epoch in range(100):  # Use more epochs for final training
                final_model.train()
                train_loss = 0.0
                for batch_X, batch_y in train_loader:
                    batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                    optimizer.zero_grad()
                    outputs = final_model(batch_X)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
                    train_loss += loss.item()

                val_loss = 0.0
                correct_predictions = 0
                total_predictions = 0
                with torch.no_grad():
                    final_model.eval()
                    for batch_X, batch_y in val_loader:
                        batch_X, batch_y = batch_X.to(device), batch_y.to(
                            device
                        )
                        outputs = final_model(batch_X)
                        val_loss += criterion(outputs, batch_y).item()

                        # Error analysis
                        error = torch.abs(outputs - batch_y)
                        within_range = error <= 2
                        correct_predictions += within_range.sum().item()
                        total_predictions += len(batch_y)

                val_accuracy = (correct_predictions / total_predictions) * 100
                train_mae = train_loss / len(train_loader)
                val_mae = val_loss / len(val_loader)
                mae_difference = abs(train_mae - val_mae)

                print(
                    f"Final Model - Epoch {epoch + 1}: "
                    f"Train Loss = {train_loss:.4f}, "
                    f"Validation Loss = {val_loss:.4f}, "
                    f"Validation Accuracy = {val_accuracy:.2f}%, "
                    f"MAE Difference = {mae_difference:.4f}"
                )

            # Save final model
            torch.save(final_model.state_dict(), model_path)
            print(f"Final model saved at {model_path}.")

            # Save training status
            training_status = {
                "iteration": iteration,
                "train_mae": train_mae,
                "val_mae": val_mae,
                "last_updated": datetime.now().isoformat(),
                "best_params": best_params,
            }
            with open(status_json_path, "w") as f:
                json.dump(training_status, f, indent=4)
            print(f"Training status saved at {status_json_path}.")

            mae = train_mae

            if mae <= 2:
                print("Model achieved target MAE. Training complete.")
                break

    except Exception as e:
        print(f"Error during training: {str(e)}")
        import traceback

        traceback.print_exc()

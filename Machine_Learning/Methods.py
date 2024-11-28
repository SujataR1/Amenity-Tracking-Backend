import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import make_scorer
import joblib
from tortoise.transactions import in_transaction
from tortoise.functions import Avg
from datetime import datetime
import calendar
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
                    "nineteen",
                    "one",
                    "two",
                    "three",
                    "seven",
                    "eighteen",
                )

                batch_data = pd.merge(
                    pd.DataFrame(consumption_batch),
                    pd.DataFrame(questionnaire_batch),
                    on="user_id",
                    how="left",
                )
                batch_data = pd.merge(
                    batch_data,
                    pd.DataFrame(users_batch),
                    left_on="user_id",
                    right_on="id",
                    how="left",
                )
                merged_data.append(batch_data)
                offset += batch_size

            if merged_data:
                final_data = pd.concat(merged_data, ignore_index=True)
            else:
                raise ValueError("No data available for training.")

            print(f"Final data shape: {final_data.shape}")
            processed_data = feature_engineering(final_data)

            if processed_data.empty:
                raise ValueError(
                    "Processed data is empty after feature engineering."
                )

            # Define features and target
            feature_names = [
                "month",
                "zip_avg",
                "zip_trend",
                "nineteen_avg",
                "nineteen_trend",
                "prev_consumption",
                "one",
                "two",
                "three",
                "seven",
                "eighteen",
                "month_zip_interaction",
                "month_nineteen_interaction",
                "zip_trend_nineteen_trend_interaction",
                "prev_consumption_month_interaction",
                "month_sin",
                "month_cos",
            ]
            X = processed_data[feature_names]
            y = processed_data["electricity_consumption"]

            print(f"Target variable (y) shape: {y.shape}")

            y = np.log1p(y)
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

                # Define the Optuna objective function
                def objective(trial):
                    # Suggest hyperparameters
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

                    # Adjust DataLoader for batch size
                    train_loader = DataLoader(
                        train_dataset, batch_size=batch_size, shuffle=True
                    )
                    val_loader = DataLoader(val_dataset, batch_size=batch_size)

                    # Define the model
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
                    criterion = nn.MSELoss()

                    # Train the model
                    for epoch in range(epochs):
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

                        # Validation
                        model.eval()
                        val_loss = 0.0
                        correct_predictions = 0
                        total_predictions = 0
                        with torch.no_grad():
                            for batch_X, batch_y in val_loader:
                                batch_X, batch_y = batch_X.to(
                                    device
                                ), batch_y.to(device)
                                outputs = model(batch_X)
                                loss = criterion(outputs, batch_y)
                                val_loss += loss.item()

                                # Error analysis
                                error = torch.abs(outputs - batch_y)
                                within_range = error <= 2
                                correct_predictions += (
                                    within_range.sum().item()
                                )
                                total_predictions += len(batch_y)

                        val_accuracy = (
                            correct_predictions / total_predictions * 100
                        )

                        print(
                            f"Trial {trial.number} - Epoch {epoch + 1}: "
                            f"Train Loss = {train_loss / len(train_loader):.4f}, "
                            f"Validation Loss = {val_loss / len(val_loader):.4f}, "
                            f"Validation Accuracy = {val_accuracy:.2f}%"
                        )

                    return val_loss / len(val_loader)

                # Run the Optuna study
                study = optuna.create_study(direction="minimize")
                study.optimize(objective, n_trials=100)

                # Get the best parameters
                best_params = study.best_params
                print(f"Best parameters: {best_params}")

                # Save the best parameters to a file
                with open(hyperparam_config_path, "w") as config_file:
                    json.dump(best_params, config_file, indent=4)
                print(f"Hyperparameters saved to {hyperparam_config_path}")

            # Train the final model with the best hyperparameters
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
            criterion = nn.MSELoss()

            for epoch in range(best_params["epochs"]):
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

                # Validation
                final_model.eval()
                val_loss = 0.0
                correct_predictions = 0
                total_predictions = 0
                with torch.no_grad():
                    for batch_X, batch_y in val_loader:
                        batch_X, batch_y = batch_X.to(device), batch_y.to(
                            device
                        )
                        outputs = final_model(batch_X)
                        loss = criterion(outputs, batch_y)
                        val_loss += loss.item()

                        # Count correct predictions
                        correct_predictions += (
                            (torch.abs(outputs - batch_y) < 0.05).sum().item()
                        )
                        total_predictions += len(batch_y)

                val_accuracy = correct_predictions / total_predictions * 100

                print(
                    f"Final Model - Epoch {epoch + 1}: "
                    f"Train Loss = {train_loss / len(train_loader):.4f}, "
                    f"Validation Loss = {val_loss / len(val_loader):.4f}, "
                    f"Validation Accuracy = {val_accuracy:.2f}%"
                )

            # Save the final model
            torch.save(final_model.state_dict(), model_path)
            print(f"Final model saved at {model_path}.")

            # Save the features
            with open(features_path, "w") as features_file:
                json.dump(feature_names, features_file, indent=4)
            print(f"Features saved at {features_path}.")

            # Evaluate the final model
            final_model.eval()
            y_train_pred = []
            y_val_pred = []
            with torch.no_grad():
                for batch_X, _ in train_loader:
                    batch_X = batch_X.to(device)
                    preds = final_model(batch_X)
                    y_train_pred.extend(preds.cpu().numpy())

                for batch_X, _ in val_loader:
                    batch_X = batch_X.to(device)
                    preds = final_model(batch_X)
                    y_val_pred.extend(preds.cpu().numpy())

            y_train_pred = np.expm1(y_train_pred)
            y_val_pred = np.expm1(y_val_pred)
            train_mae = mean_absolute_error(
                np.expm1(y[:train_size]), y_train_pred
            )
            val_mae = mean_absolute_error(np.expm1(y[train_size:]), y_val_pred)

            print(
                f"Iteration {iteration} - Train MAE={train_mae:.4f}, "
                f"Validation MAE={val_mae:.4f}"
            )

            mae = train_mae

            # Save training status
            training_status = {
                "iteration": iteration,
                "train_mae": train_mae,
                "val_mae": val_mae,
                "last_updated": datetime.now().isoformat(),
                "best_params": best_params,
            }
            with open(status_json_path, "w") as status_file:
                json.dump(training_status, status_file, indent=4)
            print(f"Training status saved at {status_json_path}.")

            if mae <= 3:
                print("Model achieved target MAE. Training complete.")
                break

    except Exception as e:
        print(f"Error during training: {str(e)}")


# ---------------------------------------------
# Method 3: Feature Engineering
# ---------------------------------------------


def feature_engineering(data):
    """
    Applies feature engineering to prepare data for ML model training.
    """
    # Ensure the target column is not accidentally dropped
    if "electricity_consumption" not in data.columns:
        raise ValueError(
            "Target column 'electricity_consumption' is missing in input data."
        )

    # Convert month names to numerical values
    data["month"] = data["month"].apply(
        lambda x: list(calendar.month_name).index(x)
    )

    # Add rolling averages for 'nineteen'
    data["nineteen_avg"] = data.groupby(["nineteen", "year"])[
        "electricity_consumption"
    ].transform("mean")
    data["nineteen_trend"] = data.groupby("nineteen")[
        "nineteen_avg"
    ].transform(lambda x: x.rolling(window=3, min_periods=1).mean())

    # Add ZIP code-level adjustments (fallback to nineteen)
    data["zip_avg"] = data.groupby(["pin_code", "year"])[
        "electricity_consumption"
    ].transform("mean")
    data["zip_avg"] = data["zip_avg"].fillna(data["nineteen_avg"])
    data["zip_trend"] = data.groupby("pin_code")["zip_avg"].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    data["zip_trend"] = data["zip_trend"].fillna(data["nineteen_trend"])

    # Create lag features for user-specific patterns
    data = data.sort_values(by=["user_id", "year", "month"])
    data["prev_consumption"] = data.groupby("user_id")[
        "electricity_consumption"
    ].shift(1)

    # Add interaction features
    data["month_zip_interaction"] = data["month"] * data["zip_avg"]
    data["month_nineteen_interaction"] = data["month"] * data["nineteen_avg"]
    data["zip_trend_nineteen_trend_interaction"] = (
        data["zip_trend"] * data["nineteen_trend"]
    )
    data["prev_consumption_month_interaction"] = (
        data["prev_consumption"] * data["month"]
    )

    # Add cyclical encoding for months
    data["month_sin"] = np.sin(2 * np.pi * data["month"] / 12)
    data["month_cos"] = np.cos(2 * np.pi * data["month"] / 12)

    # Drop rows with insufficient data for training
    data = data.dropna(subset=["prev_consumption"])

    return data

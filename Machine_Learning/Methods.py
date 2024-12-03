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
    WaterConsumption,
    FuelConsumption,
    GasConsumption,
    QuestionnaireAnswers,
    User,
)
from decouple import config

cudnn.benchmark = True  # Optimize GPU kernel selection for CUDA


class ConsumptionModel(nn.Module):
    def __init__(
        self,
        num_users,
        input_dim,
        hidden_dim1,
        hidden_dim2,
        embedding_dim=50,
        dropout_rate=0.2,
    ):
        super(ConsumptionModel, self).__init__()
        # Embedding layer for user_id
        self.user_embedding = nn.Embedding(num_users, embedding_dim)

        # Feedforward layers for other input features + user embedding
        self.fc1 = nn.Linear(input_dim + embedding_dim, hidden_dim1)
        self.dropout1 = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(hidden_dim1, hidden_dim2)
        self.dropout2 = nn.Dropout(dropout_rate)
        self.fc3 = nn.Linear(hidden_dim2, 1)

    def forward(self, user_ids, features):
        # Get the user embeddings
        user_embeds = self.user_embedding(user_ids)

        # Concatenate user embeddings with other features
        x = torch.cat((features, user_embeds), dim=1)

        # Pass through feedforward layers
        x = torch.relu(self.fc1(x))
        x = self.dropout1(x)
        x = torch.relu(self.fc2(x))
        x = self.dropout2(x)
        x = self.fc3(x)
        return x


async def retrain_model(resource_type: str):
    """
    Retrains the electricity consumption prediction model using PyTorch
    and Optuna for hyperparameter tuning. Includes user_id embeddings,
    Winsorization for outlier handling, and robust error handling.
    """

    # Paths for model, scaler, and metadata
    with open(
        "Machine_Learning\Machine_Learning_Parameter_Schemas.json", "r"
    ) as file:
        machine_learning_parameter_schemas = json.loads(file.read())

    config = machine_learning_parameter_schemas.get(resource_type)
    if not config:
        raise ValueError(
            f"Configuration for resource type '{resource_type}' not found."
        )

    # Paths for model, scaler, and metadata
    model_dir = config["Directory_Path"]
    model_path = path.join(model_dir, config["Trained_Model_Name"])
    scaler_path = path.join(model_dir, config["Scaler_File_Name"])
    features_path = path.join(model_dir, config["Features_File_Name"])
    user_id_mapping_path = path.join(
        model_dir, config["User_ID_Mapping_File_Name"]
    )
    pin_code_mapping_path = path.join(
        model_dir, config["PIN_Code_Mapping_Path"]
    )
    hyperparam_config_path = path.join(
        model_dir, config["Hyperparameter_Configuration_File_Name"]
    )
    status_json_path = path.join(
        model_dir, config["Model_Training_Status_File_Name"]
    )

    # Database and column details
    database_name = config["Database_Name"]
    target_column = config["Column_Name"]

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
        total_memory = torch.cuda.get_device_properties(0).total_memory
        torch.cuda.set_per_process_memory_fraction(0.75, 0)

    try:
        while mae > 2 and (time() - start_time) < max_duration:
            iteration += 1
            print(f"Retraining iteration {iteration} for {resource_type}...")

            # Fetch and preprocess data
            offset = 0
            batch_size = 25
            merged_data = []
            pin_code_mapping = {}
            pin_code_counter = 0

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
                consumption_batch = (
                    await globals()[database_name]
                    .filter(user_id__in=user_ids)
                    .values(
                        "user_id",
                        "year",
                        "month",
                        target_column,
                    )
                )
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

                # Add PIN code mapping
                for user in users_batch:
                    pin_code = user["pin_code"]
                    if pin_code not in pin_code_mapping:
                        pin_code_mapping[pin_code] = pin_code_counter
                        pin_code_counter += 1

                # Add categorical PIN codes to consumption data
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
                        consumption["pin_code_category"] = pin_code_mapping[
                            user_entry["pin_code"]
                        ]

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
                raise ValueError(
                    f"No data available for training {resource_type}."
                )

            # Handle missing data
            final_data.fillna(0, inplace=True)
            print(f"Final data shape: {final_data.shape} for {resource_type}")

            # Winsorize outliers
            lower_limit = final_data[target_column].quantile(0.01)
            upper_limit = final_data[target_column].quantile(0.99)
            final_data[target_column] = np.clip(
                final_data[target_column], lower_limit, upper_limit
            )

            # Encode categorical features
            final_data = pd.get_dummies(
                final_data,
                columns=["month", "nineteen", "seventeen"],
                prefix=["month", "climate", "vacation_month"],
            )

            # Map user_ids to integers for embedding
            user_id_mapping = {
                user_id: idx
                for idx, user_id in enumerate(final_data["user_id"].unique())
            }
            final_data["user_id"] = final_data["user_id"].map(user_id_mapping)

            # Save the mapping for inference
            with open(user_id_mapping_path, "wb") as f:
                pickle.dump(user_id_mapping, f)

            # Save the PIN code mapping for inference
            with open(pin_code_mapping_path, "wb") as f:
                pickle.dump(pin_code_mapping, f)

            # Define features and target
            feature_names = [
                "year",
                "pin_code_category",  # Use the categorical PIN code
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
            y = final_data[target_column]

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
            user_id_tensor = torch.tensor(
                final_data["user_id"].values, dtype=torch.long
            ).to(device)
            feature_tensor = torch.tensor(X_scaled, dtype=torch.float32).to(
                device
            )
            target_tensor = (
                torch.tensor(y.values, dtype=torch.float32)
                .view(-1, 1)
                .to(device)
            )

            dataset = TensorDataset(
                user_id_tensor, feature_tensor, target_tensor
            )
            train_size = int(0.8 * len(dataset))
            val_size = len(dataset) - train_size
            train_dataset, val_dataset = torch.utils.data.random_split(
                dataset, [train_size, val_size]
            )

            train_loader = DataLoader(
                train_dataset, batch_size=32, shuffle=True
            )
            val_loader = DataLoader(val_dataset, batch_size=32)

            # Define the Optuna optimization objective
            def objective(trial):
                # Trial parameters for the neural network
                learning_rate = trial.suggest_float(
                    "learning_rate", 1e-5, 1e-2, log=True
                )
                hidden_dim1 = trial.suggest_int(
                    "hidden_dim1", 64, 512, step=32
                )
                hidden_dim2 = trial.suggest_int(
                    "hidden_dim2", 32, 256, step=16
                )
                embedding_dim = trial.suggest_int(
                    "embedding_dim", 10, 100, step=10
                )
                dropout_rate = trial.suggest_float(
                    "dropout_rate", 0.1, 0.5, step=0.1
                )
                weight_decay = trial.suggest_float(
                    "weight_decay", 1e-6, 1e-3, log=True
                )
                epochs = trial.suggest_int(
                    "epochs",
                    30,
                    100,
                    step=5,  # Tune number of epochs between 10 and 50
                )

                model = ConsumptionModel(
                    num_users=len(user_id_mapping),
                    input_dim=len(feature_names),
                    hidden_dim1=hidden_dim1,
                    hidden_dim2=hidden_dim2,
                    embedding_dim=embedding_dim,
                    dropout_rate=dropout_rate,
                ).to(device)
                optimizer = optim.Adam(
                    model.parameters(),
                    lr=learning_rate,
                    weight_decay=weight_decay,
                )
                criterion = nn.L1Loss()
                model.to(device)

                for epoch in range(
                    epochs
                ):  # Optuna limits epochs for faster trials
                    model.train()
                    train_loss = 0.0
                    train_errors = []
                    correct_predictions = 0
                    total_predictions = 0

                    # Training loop
                    for user_ids, features, targets in train_loader:
                        user_ids, features, targets = (
                            user_ids.to(device),
                            features.to(device),
                            targets.to(device),
                        )
                        optimizer.zero_grad()
                        outputs = model(user_ids, features)
                        loss = criterion(outputs, targets)
                        loss.backward()
                        optimizer.step()
                        train_loss += loss.item()

                        # Track train errors and accuracy
                        error = torch.abs(outputs - targets)
                        train_errors.extend(error.cpu().detach().numpy())
                        within_range = error <= 2  # Predictions within ±2 kWh
                        correct_predictions += within_range.sum().item()
                        total_predictions += len(targets)

                    # Calculate training metrics
                    train_mae = np.mean(train_errors)
                    train_accuracy = (
                        correct_predictions / total_predictions
                    ) * 100

                    # Validation loop
                    val_loss = 0.0
                    val_errors = []
                    correct_predictions = 0
                    total_predictions = 0

                    with torch.no_grad():
                        model.eval()
                        for user_ids, features, targets in val_loader:
                            user_ids, features, targets = (
                                user_ids.to(device),
                                features.to(device),
                                targets.to(device),
                            )
                            outputs = model(user_ids, features)
                            loss = criterion(outputs, targets.to(device))
                            val_loss += loss.item()

                            # Track validation errors and accuracy
                            error = torch.abs(outputs - targets)
                            val_errors.extend(error.cpu().detach().numpy())
                            within_range = (
                                error <= 2
                            )  # Predictions within ±2 kWh
                            correct_predictions += within_range.sum().item()
                            total_predictions += len(targets)

                    # Calculate validation metrics
                    val_mae = np.mean(val_errors)
                    val_accuracy = (
                        correct_predictions / total_predictions
                    ) * 100

                    # Calculate MAE difference
                    mae_difference = abs(train_mae - val_mae)

                    # Print metrics
                    print(
                        f"Trial {trial.number} - Epoch {epoch + 1}/{epochs}: "
                        f"Train Loss = {train_loss:.4f}, "
                        f"Validation Loss = {val_loss:.4f}, "
                        f"Train MAE = {train_mae:.4f}, "
                        f"Validation MAE = {val_mae:.4f}, "
                        f"MAE Difference = {mae_difference:.4f}, "
                        f"Training Accuracy = {train_accuracy:.4f}, "
                        f"Validation Accuracy = {val_accuracy:.2f}%"
                    )

                return val_loss / len(val_loader)

            # Run Optuna optimization
            study = optuna.create_study(direction="minimize")
            study.optimize(objective, n_trials=15, n_jobs=-1)

            # Save best parameters
            best_params = study.best_params
            print(f"Best hyperparameters: {best_params}")
            with open(hyperparam_config_path, "w") as f:
                json.dump(best_params, f, indent=4)

            # Train final model
            final_model = ConsumptionModel(
                num_users=len(user_id_mapping),
                input_dim=len(feature_names),
                hidden_dim1=best_params["hidden_dim1"],
                hidden_dim2=best_params["hidden_dim2"],
                embedding_dim=best_params["embedding_dim"],
                dropout_rate=best_params["dropout_rate"],
            ).to(device)

            criterion = nn.L1Loss()

            optimizer = optim.Adam(
                final_model.parameters(),
                lr=best_params["learning_rate"],
                weight_decay=best_params["weight_decay"],
            )
            final_model.to(device)
            final_model.train()

            for epoch in range(
                best_params["epochs"]
            ):  # Use more epochs for final training
                train_loss = 0.0
                train_errors = []
                correct_predictions = 0
                total_predictions = 0

                # Training loop
                for user_ids, features, targets in train_loader:
                    user_ids, features, targets = (
                        user_ids.to(device),
                        features.to(device),
                        targets.to(device),
                    )
                    optimizer.zero_grad()
                    outputs = final_model(user_ids, features)
                    loss = criterion(outputs, targets.to(device))
                    loss.backward()
                    optimizer.step()
                    train_loss += loss.item()

                    # Track train errors and accuracy
                    error = torch.abs(outputs - targets)
                    train_errors.extend(error.cpu().detach().numpy())
                    within_range = error <= 2  # Predictions within ±2 kWh
                    correct_predictions += within_range.sum().item()
                    total_predictions += len(targets)

                # Calculate training metrics
                train_mae = np.mean(train_errors)
                train_accuracy = (
                    correct_predictions / total_predictions
                ) * 100

                # Validation loop
                val_loss = 0.0
                val_errors = []
                correct_predictions = 0
                total_predictions = 0

                with torch.no_grad():
                    final_model.eval()
                    for user_ids, features, targets in val_loader:
                        user_ids, features, targets = (
                            user_ids.to(device),
                            features.to(device),
                            targets.to(device),
                        )
                        outputs = final_model(user_ids, features)
                        val_loss += criterion(outputs, targets).item()

                        # Track validation errors and accuracy
                        error = torch.abs(outputs - targets)
                        val_errors.extend(error.cpu().detach().numpy())
                        within_range = error <= 2  # Predictions within ±2 kWh
                        correct_predictions += within_range.sum().item()
                        total_predictions += len(targets)

                # Calculate validation metrics
                val_mae = np.mean(val_errors)
                val_accuracy = (correct_predictions / total_predictions) * 100

                # Calculate MAE difference
                mae_difference = abs(train_mae - val_mae)

                # Print metrics
                print(
                    f"Final Model - Epoch {epoch + 1}/100: "
                    f"Train Loss = {train_loss:.4f}, "
                    f"Validation Loss = {val_loss:.4f}, "
                    f"Train MAE = {train_mae:.4f}, "
                    f"Validation MAE = {val_mae:.4f}, "
                    f"MAE Difference = {mae_difference:.4f}, "
                    f"Train Accuracy = {train_accuracy:.4f}, "
                    f"Validation Accuracy = {val_accuracy:.2f}%"
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

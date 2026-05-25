# Machine_Learning/evaluation.py

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


def evaluate_model(y_test, predictions):

    mae = mean_absolute_error(y_test, predictions)

    mse = mean_squared_error(y_test, predictions)

    rmse = mse ** 0.5

    r2 = r2_score(y_test, predictions)

    print("\n========== MODEL EVALUATION ==========")

    print(f"MAE  : {mae}")

    print(f"MSE  : {mse}")

    print(f"RMSE : {rmse}")

    print(f"R2   : {r2}")

    print("======================================\n")

    return {
        "mae": mae,
        "mse": mse,
        "rmse": rmse,
        "r2": r2,
    }
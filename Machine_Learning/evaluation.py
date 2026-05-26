# Machine_Learning/evaluation.py
import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


# =========================================================
# SAFE MAPE (STABLE VERSION)
# =========================================================
def mean_absolute_percentage_error(y_true, y_pred):

    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    epsilon = 1e-8  # prevents division instability

    denominator = np.maximum(np.abs(y_true), epsilon)

    mape = np.mean(np.abs((y_true - y_pred) / denominator)) * 100

    return float(mape)


# =========================================================
# MAIN EVALUATION FUNCTION
# =========================================================
def evaluate_model(y_test, predictions):

    # -----------------------------------------------------
    # CORE METRICS
    # -----------------------------------------------------
    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, predictions)
    mape = mean_absolute_percentage_error(y_test, predictions)

    # -----------------------------------------------------
    # NO FAKE ACCURACY (IMPORTANT FIX)
    # -----------------------------------------------------
    # Regression does NOT have accuracy %
    # We intentionally remove misleading metric

    # -----------------------------------------------------
    # RAW METRICS (for system use)
    # -----------------------------------------------------
    results_raw = {
        "mae": float(mae),
        "mse": float(mse),
        "rmse": float(rmse),
        "r2": float(r2),
        "mape_percentage": float(mape),
    }

    # -----------------------------------------------------
    # ROUNDED METRICS (for UI / logging)
    # -----------------------------------------------------
    results_rounded = {
        "mae": round(mae, 4),
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "mape_percentage": round(mape, 4),
    }

    # -----------------------------------------------------
    # LOGGING
    # -----------------------------------------------------
    print("\n========== MODEL EVALUATION ==========\n")

    print(f"MAE     : {results_rounded['mae']}")
    print(f"MSE     : {results_rounded['mse']}")
    print(f"RMSE    : {results_rounded['rmse']}")
    print(f"R2      : {results_rounded['r2']}")
    print(f"MAPE %  : {results_rounded['mape_percentage']}")

    print("\n======================================\n")

    # -----------------------------------------------------
    # RETURN BOTH (BEST PRACTICE)
    # -----------------------------------------------------
    return {
        "raw": results_raw,
        "rounded": results_rounded,
    }


# =========================================================
# TESTING
# =========================================================
if __name__ == "__main__":

    y_true = [100, 200, 300, 400, 500]
    y_pred = [110, 190, 310, 395, 520]

    results = evaluate_model(y_true, y_pred)

    print(results)
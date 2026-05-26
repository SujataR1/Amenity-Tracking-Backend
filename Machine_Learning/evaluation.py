# Machine_Learning/evaluation.py

import numpy as np

from sklearn.metrics import (

    mean_absolute_error,

    mean_squared_error,

    r2_score,
)


# =========================================================
# SAFE MAPE
# =========================================================
def mean_absolute_percentage_error(
    y_true,
    y_pred,
):

    y_true = np.array(y_true)

    y_pred = np.array(y_pred)

    # -----------------------------------------------------
    # AVOID DIVISION BY ZERO
    # -----------------------------------------------------
    non_zero_mask = y_true != 0

    y_true = y_true[non_zero_mask]

    y_pred = y_pred[non_zero_mask]

    if len(y_true) == 0:
        return 0

    mape = np.mean(
        np.abs((y_true - y_pred) / y_true)
    ) * 100

    return mape


# =========================================================
# MODEL EVALUATION
# =========================================================
def evaluate_model(
    y_test,
    predictions,
):

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------
    mae = mean_absolute_error(
        y_test,
        predictions,
    )

    mse = mean_squared_error(
        y_test,
        predictions,
    )

    rmse = np.sqrt(mse)

    r2 = r2_score(
        y_test,
        predictions,
    )

    mape = mean_absolute_percentage_error(
        y_test,
        predictions,
    )

    # -----------------------------------------------------
    # ACCURACY ESTIMATION
    # -----------------------------------------------------
    accuracy = max(
        0,
        100 - mape,
    )

    # -----------------------------------------------------
    # ROUND VALUES
    # -----------------------------------------------------
    mae = round(float(mae), 4)

    mse = round(float(mse), 4)

    rmse = round(float(rmse), 4)

    r2 = round(float(r2), 4)

    mape = round(float(mape), 4)

    accuracy = round(float(accuracy), 2)

    # -----------------------------------------------------
    # LOGGING
    # -----------------------------------------------------
    print("\n========== MODEL EVALUATION ==========\n")

    print(f"MAE                : {mae}")

    print(f"MSE                : {mse}")

    print(f"RMSE               : {rmse}")

    print(f"R2 SCORE           : {r2}")

    print(f"MAPE (%)           : {mape}")

    print(f"MODEL ACCURACY (%) : {accuracy}")

    print("\n======================================\n")

    # -----------------------------------------------------
    # RETURN
    # -----------------------------------------------------
    return {

        "mae": mae,

        "mse": mse,

        "rmse": rmse,

        "r2": r2,

        "mape_percentage": mape,

        "accuracy_percentage": accuracy,
    }


# =========================================================
# TESTING
# =========================================================
if __name__ == "__main__":

    y_true = [100, 200, 300, 400, 500]

    y_pred = [110, 190, 310, 395, 520]

    results = evaluate_model(
        y_true,
        y_pred,
    )

    print(results)
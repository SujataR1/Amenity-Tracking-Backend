# Machine_Learning/feature_engineering.py

import pandas as pd
import numpy as np


# =========================================================
# SAFE BOOLEAN CONVERSION
# =========================================================
def safe_bool(value):

    if pd.isna(value):
        return 0

    if isinstance(value, str):
        return 1 if value.lower() in [
            "true",
            "1",
            "yes",
            "y",
        ] else 0

    return int(bool(value))


# =========================================================
# SAFE CLIMATE ENCODING
# =========================================================
def encode_climate(value):

    climate_map = {
        "cold": 0,
        "moderate": 1,
        "hot": 2,
    }

    if pd.isna(value):
        return 1

    return climate_map.get(str(value).lower(), 1)


# =========================================================
# CYCLICAL MONTH ENCODING
# =========================================================
def add_month_cyclical_features(df: pd.DataFrame):

    if "month" not in df.columns:
        df["month"] = 1

    df["month_sin"] = np.sin(
        2 * np.pi * df["month"] / 12
    )

    df["month_cos"] = np.cos(
        2 * np.pi * df["month"] / 12
    )

    return df


# =========================================================
# HISTORICAL FEATURE ENGINEERING
# =========================================================
def add_historical_features(
    df: pd.DataFrame,
    target_column: str = "electricity_consumption",
):

    df = df.copy()

    # -----------------------------------------------------
    # SORT DATA FOR TIME SERIES
    # -----------------------------------------------------
    sort_cols = []

    if "user_id" in df.columns:
        sort_cols.append("user_id")

    if "year" in df.columns:
        sort_cols.append("year")

    if "month" in df.columns:
        sort_cols.append("month")

    if sort_cols:
        df = df.sort_values(by=sort_cols)

    # -----------------------------------------------------
    # LAST MONTH CONSUMPTION
    # -----------------------------------------------------
    if (
        "user_id" in df.columns
        and target_column in df.columns
    ):

        df["last_month_consumption"] = (
            df.groupby("user_id")[target_column]
            .shift(1)
        )

    else:
        df["last_month_consumption"] = 0

    # -----------------------------------------------------
    # AVG LAST 3 MONTHS
    # -----------------------------------------------------
    if (
        "user_id" in df.columns
        and target_column in df.columns
    ):

        df["avg_last_3_months"] = (
            df.groupby("user_id")[target_column]
            .transform(
                lambda x: (
                    x.shift(1)
                    .rolling(3, min_periods=1)
                    .mean()
                )
            )
        )

    else:
        df["avg_last_3_months"] = 0

    # -----------------------------------------------------
    # AVG LAST 6 MONTHS
    # -----------------------------------------------------
    if (
        "user_id" in df.columns
        and target_column in df.columns
    ):

        df["avg_last_6_months"] = (
            df.groupby("user_id")[target_column]
            .transform(
                lambda x: (
                    x.shift(1)
                    .rolling(6, min_periods=1)
                    .mean()
                )
            )
        )

    else:
        df["avg_last_6_months"] = 0

    # -----------------------------------------------------
    # GROWTH RATE
    # -----------------------------------------------------
    df["consumption_growth_rate"] = (
        (
            df.get(target_column, 0)
            - df["last_month_consumption"]
        )
        /
        (
            df["last_month_consumption"]
            .replace(0, 1)
        )
    )

    # -----------------------------------------------------
    # YEARLY AVERAGE
    # -----------------------------------------------------
    if (
        "user_id" in df.columns
        and target_column in df.columns
    ):

        df["yearly_avg_consumption"] = (
            df.groupby("user_id")[target_column]
            .transform("mean")
        )

    else:
        df["yearly_avg_consumption"] = 0

    # -----------------------------------------------------
    # MAX HISTORICAL CONSUMPTION
    # -----------------------------------------------------
    if (
        "user_id" in df.columns
        and target_column in df.columns
    ):

        df["max_historical_consumption"] = (
            df.groupby("user_id")[target_column]
            .transform("max")
        )

    else:
        df["max_historical_consumption"] = 0

    # -----------------------------------------------------
    # MIN HISTORICAL CONSUMPTION
    # -----------------------------------------------------
    if (
        "user_id" in df.columns
        and target_column in df.columns
    ):

        df["min_historical_consumption"] = (
            df.groupby("user_id")[target_column]
            .transform("min")
        )

    else:
        df["min_historical_consumption"] = 0

    return df


# =========================================================
# MAIN FEATURE ENGINEERING PIPELINE
# =========================================================
def create_features(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # =====================================================
    # BOOLEAN COLUMNS
    # =====================================================
    bool_cols = [
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
        "fifteen",
        "sixteen",
    ]

    for col in bool_cols:

        if col in df.columns:
            df[col] = df[col].apply(safe_bool)

        else:
            df[col] = 0

    # =====================================================
    # SAFE NUMERIC DEFAULTS
    # =====================================================
    numeric_defaults = {
        "one": 0,
        "two": 0,
        "three": 1,
        "fourteen": 0,
        "eighteen": 0,
        "month": 1,
        "year": 2025,
    }

    for col, default in numeric_defaults.items():

        if col not in df.columns:
            df[col] = default

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        ).fillna(default)

    # =====================================================
    # CLIMATE ENCODING
    # =====================================================
    if "nineteen" in df.columns:

        df["nineteen"] = df["nineteen"].apply(
            encode_climate
        )

    else:
        df["nineteen"] = 1

    # =====================================================
    # FEATURE 1: PEOPLE PER ROOM
    # =====================================================
    df["people_per_room"] = (
        df["one"]
        /
        df["three"].replace(0, 1)
    )

    # =====================================================
    # FEATURE 2: CHILD RATIO
    # =====================================================
    df["children_ratio"] = (
        df["two"]
        /
        df["one"].replace(0, 1)
    )

    # =====================================================
    # FEATURE 3: VACATION FACTOR
    # =====================================================
    df["vacation_factor"] = (
        df["eighteen"] * 0.1
    )

    # =====================================================
    # FEATURE 4: APPLIANCE SCORE
    # =====================================================
    appliance_cols = [
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
    ]

    df["appliance_score"] = 0

    for col in appliance_cols:
        df["appliance_score"] += df[col]

    # =====================================================
    # FEATURE 5: LUXURY SCORE
    # =====================================================
    df["luxury_score"] = (
        df["fifteen"]
        + df["sixteen"]
    )

    # =====================================================
    # FEATURE 6: HOME AREA PER PERSON
    # =====================================================
    df["area_per_person"] = (
        df["fourteen"]
        /
        df["one"].replace(0, 1)
    )

    # =====================================================
    # FEATURE 7: DENSITY APPLIANCE INTERACTION
    # =====================================================
    df["density_appliance_interaction"] = (
        df["people_per_room"]
        *
        df["appliance_score"]
    )

    # =====================================================
    # FEATURE 8: CLIMATE APPLIANCE INTERACTION
    # =====================================================
    df["climate_appliance_interaction"] = (
        df["nineteen"]
        *
        df["appliance_score"]
    )

    # =====================================================
    # FEATURE 9: AREA APPLIANCE INTERACTION
    # =====================================================
    df["area_appliance_interaction"] = (
        df["fourteen"]
        *
        df["appliance_score"]
    )

    # =====================================================
    # FEATURE 10: HIGH CONSUMPTION RISK SCORE
    # =====================================================
    df["high_consumption_risk"] = (
        (
            df["appliance_score"] * 2
        )
        +
        (
            df["luxury_score"] * 3
        )
        +
        (
            df["nineteen"]
        )
        +
        (
            df["people_per_room"]
        )
    )

    # =====================================================
    # CYCLICAL MONTH FEATURES
    # =====================================================
    df = add_month_cyclical_features(df)

    # =====================================================
    # HISTORICAL FEATURES
    # =====================================================
    if "electricity_consumption" in df.columns:

        df = add_historical_features(
            df,
            target_column="electricity_consumption",
        )

    # =====================================================
    # FINAL CLEANUP
    # =====================================================
    df.replace(
        [np.inf, -np.inf],
        0,
        inplace=True,
    )

    df.fillna(0, inplace=True)

    return df
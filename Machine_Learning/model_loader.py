# Machine_Learning/model_loader.py

import os
import json
import joblib

from functools import lru_cache

from Machine_Learning.constants import (
    get_resource_config,
)


# =========================================================
# RESOURCE VALIDATION
# =========================================================
def validate_resource(resource):

    if not isinstance(resource, str):
        raise TypeError(
            "resource must be string"
        )

    return (
        resource
        .strip()
        .lower()
    )


# =========================================================
# LOAD MODEL
# =========================================================
@lru_cache(maxsize=8)
def load_model(resource):

    resource = validate_resource(
        resource
    )

    cfg = get_resource_config(
        resource
    )

    model_path = cfg[
        "model_path"
    ]

    if not os.path.exists(
        model_path
    ):
        raise FileNotFoundError(
            f"Model not found:\n{model_path}"
        )

    return joblib.load(
        model_path
    )


# =========================================================
# LOAD FEATURE NAMES
# =========================================================
@lru_cache(maxsize=8)
def load_feature_names(resource):

    resource = validate_resource(
        resource
    )

    cfg = get_resource_config(
        resource
    )

    feature_path = cfg[
        "features_path"
    ]

    if not os.path.exists(
        feature_path
    ):
        raise FileNotFoundError(
            f"Features file missing:\n{feature_path}"
        )

    with open(
        feature_path,
        "r",
    ) as f:

        data = json.load(
            f
        )

    # -------------------------
    # SUPPORT:
    # {"features":[]}
    # []
    # -------------------------

    if (
        isinstance(
            data,
            dict
        )
        and "features"
        in data
    ):

        features = (
            data[
                "features"
            ]
        )

    elif isinstance(
        data,
        list
    ):

        features = data

    else:

        raise ValueError(
            "Invalid feature file"
        )

    if (
        not features
    ):

        raise ValueError(
            "Empty features"
        )

    return features


# =========================================================
# LOAD ARTIFACTS
# =========================================================
def load_model_artifacts(
    resource
):

    return {

        "resource":
            resource,

        "model":
            load_model(
                resource
            ),

        "feature_names":
            load_feature_names(
                resource
            ),
    }


# =========================================================
# EXISTS CHECK
# =========================================================
def model_exists(
    resource
):

    try:

        cfg = (
            get_resource_config(
                resource
            )
        )

        return os.path.exists(
            cfg[
                "model_path"
            ]
        )

    except Exception:

        return False


# =========================================================
# TEST
# =========================================================
if __name__ == "__main__":

    RESOURCE = (
        "electricity"
    )

    print(
        "\nLoading..."
    )

    artifacts = (
        load_model_artifacts(
            RESOURCE
        )
    )

    print(
        "\nResource:",
        artifacts[
            "resource"
        ]
    )

    print(
        "\nModel:",
        type(
            artifacts[
                "model"
            ]
        )
    )

    print(
        "\nFeatures:",
        len(
            artifacts[
                "feature_names"
            ]
        )
    )

    print(
        "\nPreview:"
    )

    print(
        artifacts[
            "feature_names"
        ][:10]
    )
import os as _os
from easydict import EasyDict as _EasyDict
from utils.get_asset import get_asset_path

BASE_DIR = get_asset_path()

__BASE_DATA = "/home/ratchet/Documents/Dataset/classification"
PATH_CUBEMOS_SDK = "/opt/cubemos/skeleton_tracking/"

DATA = _EasyDict({
    "INPUTS": "%s/outputs/frames" % __BASE_DATA,
    "PATH_PEOPLE": "%s/people.json" % __BASE_DATA,
    "PATH_TAXONOMY": "data/label_hierarchy.json",
    "RESOLUTION": {
        "FRAME": (480, 640, 4)
    },
    "DEPTH": {
        "MAX": 1.5
    },
})

TRAINING = _EasyDict({
    "USE_PREPROCESSED": False,
    "BATCH_SIZE": 16,
    "TRAINGING_SET_RATIO": 0.9,
    "LEARNING_RATE_INITIAL": 1e-3,
    "EPOCHS": 50,
    "AUGMENT": True,
    "OUTPUT_MODELS": "%s/output_models" % BASE_DIR
})

MODEL = _EasyDict({
    "IN_POINTS": 2 ** 13
})
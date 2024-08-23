import os
import sys


def get_asset_path(path = None):
    if getattr(sys, "frozen", False):
        # frozen
        dir_ = os.path.dirname(sys.executable)
    else:
        # unfrozen
        dir_ = os.path.realpath(".")


    return dir_ if path is None else os.path.realpath(os.path.join(dir_, path))
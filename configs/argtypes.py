import argparse
from math import isfinite, inf


def strWithNone(v):
    return None if v == "None" else v


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def str2int_inf(v):
    value = float(v)

    return int(value) if isfinite(value) else inf

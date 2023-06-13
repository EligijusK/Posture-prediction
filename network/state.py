from easydict import EasyDict as _EasyDict
from math import inf as _inf


def create_empty_state():
    def create_loss_state():
        return {
            "loss": _inf,
            # "loss_points": _inf,
            # "loss_mask": _inf
        }

    def create_state():
        return {
            "epoch": 0,
            "train": create_loss_state(),
            "test": create_loss_state()
        }

    return _EasyDict({
        "last_state": create_state(),
        "best_state": {
            "train": create_state(),
            "test": create_state()
        }
    })


def set_state(state, *losses):
    # total, points, center = losses

    state.loss = float(losses[0])
    # state.loss_points = float(points)
    # state.loss_center = float(center)


def copy_state(to_state, from_state):
    for key, value in from_state.items():
        to_state[key] = value

import os
import imp
from network.network import Network
import configs.config as cfg


def get_network_constructor(checkpoint: str, use_stripped: bool) -> Network:
    if checkpoint is None:
        return Network

    dir_chekpoint = "%s/chk_%s" % (cfg.TRAINING.OUTPUT_MODELS, checkpoint)
    py_path = "%s/file_copies/network/__init__.py" % dir_chekpoint

    if os.path.isfile(py_path):
        module_model = imp.load_package("_network", py_path)

        return module_model.StrippedNetwork if use_stripped else module_model.Network

    return Network

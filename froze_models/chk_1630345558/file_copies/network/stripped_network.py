import os
import torch
import numpy as np
import configs.config as cfg
from .models.sit_straight import SitStraightNet as _SitStraightNet
from data.label_manager import LabelManager


class StrippedNetwork:
    def __init__(self, *, path_weights: str, label_count, device: str = "cuda"):
        model = _SitStraightNet(
            in_points=cfg.MODEL.IN_POINTS,
            use_preprocessed=cfg.TRAINING.USE_PREPROCESSED,
            label_count=label_count
        )

        self.model = model.cuda() if device == "cuda" else model.cpu()
        self.device = device

        self.restore(path_weights)

    def restore(self, path_weights):
        if path_weights.endswith(".xth"):
            import pickle
            from cryptography.fernet import Fernet
            from . import encryption_key

            with open(path_weights, "rb") as f:
                encrypted_bytes = f.read()

                fernet = Fernet(encryption_key)
                decrypted = fernet.decrypt(encrypted_bytes)

                weights = pickle.loads(decrypted)

                for key in weights:
                    t = torch.tensor(weights[key], device=self.device)
                    weights[key] = t

                self.model.load_state_dict(weights)
        else:
            state = torch.load(path_weights)
            self.model.load_state_dict(state["state_model"])

    def predict(self, t_in: np.array) -> np.array:
        ssnet = self.model

        ssnet.eval()

        with torch.no_grad():
            t_in = t_in.float()
            t_in = t_in.cuda().contiguous() if self.device == "cuda" else t_in

            t_out = ssnet(t_in)

            return torch.sigmoid(t_out)

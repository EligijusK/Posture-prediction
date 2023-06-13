import torch.nn as _tnn

class HalfPoints(_tnn.Module):
    def __init__(self):
        super(HalfPoints, self).__init__()

        self.halver = _tnn.Sequential(
            _tnn.Conv1d(6, 6, 1, 2),
            _tnn.BatchNorm1d(6),
            _tnn.ReLU(),
        )

    def forward(self, t_in):
        # return t_in[:, 0::2]
        return self.halver(t_in)

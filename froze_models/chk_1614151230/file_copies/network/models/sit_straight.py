import torch as _torch
import torch.nn as _tnn
from .pointnet_feat import PointNetfeat as _PointNetfeat
from .half_points import HalfPoints


class SitStraightNet(_tnn.Module):
    def __init__(self, *, in_points, use_preprocessed, label_count):
        super(SitStraightNet, self).__init__()

        self.needs_reset = False
        self.bottleneck_size = 32

        self.gather = _tnn.Sequential(*[HalfPoints() for x in range(0, 5)])

        self.encoder = _PointNetfeat(6)

        self.bottleneck = _tnn.Sequential(
            _tnn.Dropout(0.1),
            _tnn.Linear(1024, self.bottleneck_size),
            _tnn.BatchNorm1d(self.bottleneck_size),
            _tnn.ReLU()
        )

        self.branch = _tnn.Sequential(
            _tnn.Dropout(0.1),
            _tnn.Linear(1024, 256),
            _tnn.BatchNorm1d(256),
            _tnn.ReLU(),
            _tnn.Dropout(0.2),
            _tnn.Linear(256, 128 - self.bottleneck_size),
            _tnn.BatchNorm1d(128 - self.bottleneck_size),
            _tnn.ReLU()
        )

        self.fc = _tnn.Sequential(
            _tnn.Dropout(0.5),
            _tnn.Linear(128, label_count),
        )

    def on_before_epoch(self):
        pass

    def forward(self, t_in):
        n_batch, n_points, n_channel = t_in.shape

        x = t_in

        x = x.transpose(1, 2)
        x = self.gather(x)

        x = self.encoder(x)

        y = self.bottleneck(x)
        z = self.branch(x)

        x = _torch.cat([y, z], axis=-1)

        x = self.fc(x)

        return x

import torch as _torch
import torch.nn as _tnn
# import torchvision as _tvis
from .pointnet_feat import PointNetfeat as _PointNetfeat
from .half_points import HalfPoints


class SitStraightNet(_tnn.Module):
    def __init__(self, *, in_points, use_preprocessed, label_count):
        super(SitStraightNet, self).__init__()

        self.needs_reset = False
        # self.bottleneck_size = 32
        # self.res_bottleneck = 16

        self.bottleneck_size = 8
        self.res_bottleneck = 4

        self.channels = 6

        # self.resize = _tvis.transforms.Resize((480 >> 2, 640 >> 2))

        # self.gather = _tnn.Sequential(*[HalfPoints() for x in range(0, 6)])
        self.gather = _tnn.Sequential(
            # _tvis.transforms.Resize((480 >> 2, 640 >> 2)),
            *[HalfPoints() for x in range(0, 5)],
            # _tnn.Conv1d(6, 16, 3, 2),
            # _tnn.BatchNorm1d(16),
            # _tnn.LeakyReLU(),
            # _tnn.Dropout(0.1),
            # _tnn.Conv1d(16, 32, 3, 2),
            # _tnn.BatchNorm1d(32),
            # _tnn.LeakyReLU(),
            # _tnn.Dropout(0.1),
            # _tnn.Conv1d(32, self.channels, 3, 2),
            # _tnn.BatchNorm1d(self.channels),
            # _tnn.LeakyReLU(),
        )

        self.encoder = _PointNetfeat(self.channels)

        # self.bottleneck = _tnn.Sequential(
        #     _tnn.Dropout(0.1),
        #     _tnn.Linear(1024, self.bottleneck_size),
        #     _tnn.BatchNorm1d(self.bottleneck_size),
        #     _tnn.ReLU()
        # )

        # self.branch = _tnn.Sequential(
        #     _tnn.Dropout(0.1),
        #     _tnn.Linear(1024, 256),
        #     _tnn.BatchNorm1d(256),
        #     _tnn.ReLU(),
        #     _tnn.Dropout(0.2),
        #     _tnn.Linear(256, 128 - self.bottleneck_size),
        #     _tnn.BatchNorm1d(128 - self.bottleneck_size),
        #     _tnn.ReLU()
        # )

        # self.fc = _tnn.Sequential(
        #     _tnn.Dropout(0.5),
        #     _tnn.Linear(128, label_count),
        # )

        self.bottleneck = _tnn.Sequential(
            _tnn.Dropout(0.1),
            _tnn.Linear(1024, self.res_bottleneck),
            _tnn.BatchNorm1d(self.res_bottleneck),
            _tnn.ReLU(),
            _tnn.Dropout(0.3),
            _tnn.Linear(self.res_bottleneck, self.bottleneck_size),
            _tnn.BatchNorm1d(self.bottleneck_size),
            _tnn.ReLU()
        )

        self.branch = _tnn.Sequential(
            _tnn.Dropout(0.1),
            _tnn.Linear(1024, 256),
            _tnn.BatchNorm1d(256),
            _tnn.ReLU(),
            _tnn.Dropout(0.2),
            _tnn.Linear(256, self.bottleneck_size),
            _tnn.BatchNorm1d(self.bottleneck_size),
            _tnn.ReLU()
        )

        self.fc = _tnn.Sequential(
            _tnn.Dropout(0.5),
            _tnn.Linear(self.bottleneck_size, label_count),
        )

    def on_before_epoch(self):
        pass

    def forward(self, t_in):
        n_batch, n_points, n_channel = t_in.shape

        x = t_in

        x = x.transpose(1, 2)
        # x = x.view(-1, 6, 480, 640)
        
        # x = self.resize(x)
        # b, ch, w, h = x.shape
        # x = x.view(b, ch, w * h)

        x = self.gather(x)
        
        # b, ch, w, h = x.shape
        # x = x.view(b, ch, w * h)

        x = self.encoder(x)

        y = self.bottleneck(x)
        z = self.branch(x)

        # x = _torch.cat([y, z], axis=-1)
        x = y + z

        x = self.fc(x)

        return x

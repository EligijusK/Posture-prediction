import torch as _torch
import torch.nn as _tnn
import torch.nn.functional as _tfuncional


class PointNetfeat(_tnn.Module):
    def __init__(self, in_feats=3):
        super(PointNetfeat, self).__init__()

        self.conv1 = _tnn.Conv1d(in_feats, 64, 1)
        self.conv2 = _tnn.Conv1d(64, 128, 1)
        self.conv3 = _tnn.Conv1d(128, 1024, 1)

        self.bn1 = _tnn.BatchNorm1d(64)
        self.bn2 = _tnn.BatchNorm1d(128)
        self.bn3 = _tnn.BatchNorm1d(1024)

    def forward(self, x):
        batchsize = x.size()[0]
        x = _tfuncional.relu(self.bn1(self.conv1(x)))
        x = _tfuncional.relu(self.bn2(self.conv2(x)))
        x = self.bn3(self.conv3(x))
        x, _ = _torch.max(x, 2)
        x = x.view(-1, 1024)
        return x
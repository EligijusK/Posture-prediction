import torch as _torch
import torch.nn as _tnn
from .sit_straight import SitStraightNet as _SitStraightNet


class FullModel(_tnn.Module):
    def __init__(self, ssnet: _SitStraightNet, softmaxer):
        super(FullModel, self).__init__()

        self.ssnet = ssnet
        self.softmaxer = softmaxer

    @staticmethod
    def accuracy(output, target, softmaxer):
        """Computes the accuracy for multiple binary predictions"""
        pred = output >= 0.5
        truth = target >= 0.5
        # acc = pred.eq(truth).sum() / target.numel()

        data = [
            [name, pred[..., begin:finish].eq(truth[..., begin:finish]).sum() / target[..., begin:finish].numel()]
            for name, begin, finish in softmaxer
        ]

        return data

    def forward(self, t_data):
        t_in, t_gt = t_data

        t_pred = self.ssnet(t_in)

        with _torch.cuda.amp.autocast(enabled=False):
            pred, gt = t_pred.float(), t_gt

            bce = _tnn.functional.binary_cross_entropy_with_logits(
                pred, gt, reduction="none").mean(-1)
            acc = FullModel.accuracy(pred, gt, self.softmaxer)

        return bce, acc

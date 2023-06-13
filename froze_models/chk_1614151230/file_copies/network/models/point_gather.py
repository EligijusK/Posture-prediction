import torch as _torch
import torch.nn as _tnn
from network.modules.sampling import sampling_module as _sampling

class PointGather(_tnn.Module):
    def __init__(self, samples):
        super(PointGather, self).__init__()

        self.samples = samples
        self.module_fps = _sampling.fpsModule()
        self.module_gather = _sampling.gatherModule()

    def forward(self, t_in):
        fps_idx = self.module_fps(self.samples, t_in)
        new_xyz = self.module_gather(t_in, fps_idx)

        return new_xyz

class PointGatherColored(PointGather):
    def __init__(self, samples):
        super(PointGatherColored, self).__init__(samples)

    def forward(self, t_in):
        colors, points = t_in[..., 0:3], t_in[..., 3:6]

        fps_idx = self.module_fps(self.samples, points)
        new_xyz = self.module_gather(points, fps_idx)
        new_rgb = self.module_gather(colors, fps_idx)

        return _torch.cat([new_rgb, new_xyz], -1)

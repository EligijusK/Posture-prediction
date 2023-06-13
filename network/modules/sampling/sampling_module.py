import torch
from torch.autograd import Function
import sampling
from torch import nn

# GPU tensors only


class gatherFunction(Function):
    @staticmethod
    def forward(ctx, t_in, t_idx, t_out):
        result = sampling.gather_forward(t_in, t_idx, t_out)

        if result != 1:
            raise Exception(
                "Internal error. Returned: %i expected 1." % result)

        ctx.save_for_backward(t_in, t_idx, t_out)

        return t_out

    @staticmethod
    def backward(ctx, gradidx):
        t_in, t_idx, t_out = ctx.saved_tensors

        b, n, p = t_in.shape

        gradxyz = torch.zeros([b, n, 3]).cuda().contiguous()

        sampling.gather_backward(t_in, t_idx, t_out, gradidx.contiguous(), gradxyz)

        return gradxyz, None, None


class gatherModule(nn.Module):
    def __init__(self):
        super(gatherModule, self).__init__()

    def forward(self, t_in, t_idx):
        in_size = t_in.shape

        if len(in_size) != 3:
            raise Exception("Tensor must be of rank 3.")

        b, n, p = in_size

        if p != 3:
            raise Exception(
                "GatherPoint expects (batch_size, num_points, 3) inp shape")

        _, m = t_idx.shape

        t_out = torch.empty([b, m, 3], dtype=t_in.dtype,
                            requires_grad=True, device=t_in.device)

        result = gatherFunction.apply(t_in, t_idx, t_out)

        return result


class fpsModule(nn.Module):
    def __init__(self):
        super(fpsModule, self).__init__()

    def forward(self, npoints, t_in):
        size = t_in.shape

        if len(size) != 3:
            raise Exception("Tensor must be of rank 3.")

        b, n, p = size

        if p != 3:
            raise Exception(
                "FarthestPointSample expects (batch_size, num_points, 3) inp shape")

        t_out = torch.empty([b, npoints], dtype=torch.int32).cuda()

        result = sampling.farhest_point_sampling(npoints, t_in, t_out)

        if result != 1:
            raise Exception(
                "Internal error. Returned: %i expected 1." % result)

        return t_out


if __name__ == "__main__":
    assert torch.cuda.is_available()

    t_in = torch.rand([1, 128, 3], dtype=torch.float32).cuda()

    fps_module = fpsModule().cuda()
    gather_module = gatherModule().cuda()

    t_idx = fps_module(64, t_in)
    t_xyz = gather_module(t_in, t_idx)

    t_xyz.sum().backward()

    print("Done")

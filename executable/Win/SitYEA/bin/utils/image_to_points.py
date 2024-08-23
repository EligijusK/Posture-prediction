from numpy import float32 as _float32
from numpy import reshape as _reshape
from utils.math import depth_to_cloud

def image_to_points(frame, matrix_K, depth_scale, depth_max):
    _w, _h, _ = frame.shape

    _fx, _fy = matrix_K[0, 0], matrix_K[1, 1]
    _cx, _cy = matrix_K[0, 2], matrix_K[1, 2]

    depth = frame[..., 3] = frame[..., 3] * depth_scale
    mask = depth > depth_max

    frame[mask] = 0

    point_cloud = depth_to_cloud(
        _w, _h, _fx, _fy, _cx, _cy, frame, dtype=_float32)

    return _reshape(point_cloud, [-1, 6])
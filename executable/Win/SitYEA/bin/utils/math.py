from numpy import pi as _pi
from numpy import dot as _dot
from numpy import clip as _clip
from numpy import shape as _shape
from numpy import arccos as _acos
from numpy import indices as _indices
from numpy import newaxis as _newaxis
from numpy import float32 as _float32
from numpy.random import seed as _seed
from numpy.linalg import norm as _vlen
from numpy import concatenate as _concat_np

DEG2RAD = _pi / 180
RAD2DEG = 180 / _pi


def unit_vector(vector): return vector / _vlen(vector)
def reseed_rng(seed): _seed(seed)


def calc_angle(v1, v2):
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return _acos(_clip(_dot(v1_u, v2_u), -1.0, 1.0))


def depth_to_cloud(w, h, fx, fy, cx, cy, frame, dtype=_float32):
    _concat = _concat_np

    height, width, _ = _shape(frame)
    depth = frame[..., 3]
    indices = _indices((height, width), dtype=dtype)
    indices_y, indices_x = indices

    xs = -(indices_x - cx) * depth / fx
    ys = -(indices_y - cy) * depth / fy
    zs = depth

    points = _concat([
        xs[..., _newaxis],
        ys[..., _newaxis],
        zs[..., _newaxis]
    ], axis=2)

    colors = frame[..., 0:3]

    combined = _concat([colors, points], -1)

    return combined

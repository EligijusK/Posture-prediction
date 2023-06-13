import io as _io
import struct as _struct
import numpy as _np

"""
ply
format binary_little_endian 1.0
element vertex n
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
...
"""


def export_ply(path, points):
    with open(path, "wb") as f:
        point_count = len(points)
        header = [
            "ply",
            "format binary_little_endian 1.0",
            "element vertex %i" % point_count,
            "property float x",
            "property float y",
            "property float z",
            "property uchar red",
            "property uchar green",
            "property uchar blue",
            "end_header",
        ]

        for line in header:
            binary = ("%s\n" % line).encode("ascii")
            f.write(binary)

        for pts in points:
            color, depth = pts[0:3], pts[3:6]

            color = _np.array(color * 255, dtype=_np.uint8)
            color = _np.reshape(color, -1).tolist()
            depth = _np.reshape(depth, -1).tolist()

            depth = _struct.pack("f" * 3, *depth)
            f.write(depth)

            color = _struct.pack("B" * 3, *color)
            f.write(color)

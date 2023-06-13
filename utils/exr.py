import OpenEXR as _OpenEXR
import Imath as _Imath
import array as _array
import numpy as _np

_FLOAT = _Imath.PixelType(_Imath.PixelType.FLOAT)


def read_exr(path, channels):
    file = _OpenEXR.InputFile(path)

    header = file.header()
    window_size = header["displayWindow"]
    channels = header["channels"]
    width, height = window_size.max.x + 1, window_size.max.y + 1

    contents = _np.empty([height, width, len(channels)], dtype=_np.float32)

    channel_data = file.channels(channels, _FLOAT)

    for i, ch in enumerate(channel_data):
        contents[..., i] = _np.reshape(_np.fromstring(
            ch, dtype=_np.float32), (height, width))

    file.close()

    return contents
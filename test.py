import ctypes
import mmap
import numpy as np

WIDTH, HEIGHT = 640, 480

if __name__ == "__main__":
    SZ_DEPTH = WIDTH * HEIGHT * 1 * ctypes.sizeof(ctypes.c_float)
    SZ_OFFSET = mmap.ALLOCATIONGRANULARITY - SZ_DEPTH % mmap.ALLOCATIONGRANULARITY
    # with open("", "wb") as f:
    #     f.write(b"llll")
    with open("/Users/eligijus/.sock", "wb") as f:
        f.write(np.zeros([HEIGHT, WIDTH], dtype=np.float32))
        f.write(b"\x00" * SZ_OFFSET)  # padding for wangblows
        f.write(np.full([HEIGHT, WIDTH, 4], 255, dtype=np.uint8))
import os
import cv2
import sys
import mmap
import time
import struct
import ctypes
import asyncio
import socketio
import numpy as np
import pyrealsense2 as rs
from rs.pipeline import RSPipeLine
from utils.fetch_string import fetch_string
from utils.fetch_cameras import fetch_all_cameras
from rs.config import create_config, create_playback_config
from rs.exceptions import NoDeviceException, USB30Exception, DevInUseException

WIDTH, HEIGHT = 640, 480
# override_device = "/home/ratchet/Downloads/RS_D435I_20210428_175414.bag"
# override_device = "/home/ratchet/Downloads/Telegram Desktop/bandicam 2022-11-15 06-13-54-394.mp4"


class ModuleComs:
    def __init__(self, path_ram):
        self.hram_depth = None
        self.hram_rgba = None
        self.hfile = None

        SZ_DEPTH = WIDTH * HEIGHT * 1 * ctypes.sizeof(ctypes.c_float)
        SZ_RGB = WIDTH * HEIGHT * 4 * ctypes.sizeof(ctypes.c_uint8)
        SZ_OFFSET = mmap.ALLOCATIONGRANULARITY - SZ_DEPTH % mmap.ALLOCATIONGRANULARITY

        print("OS requires offset offset of '%i' bytes" % SZ_OFFSET)
        sys.stdout.flush()

        # initialize socket
        with open(path_ram, "wb") as f:
            f.write(np.zeros([HEIGHT, WIDTH], dtype=np.float32))
            f.write(b"\x00" * SZ_OFFSET)  # padding for wangblows
            f.write(np.full([HEIGHT, WIDTH, 4], 255, dtype=np.uint8))

        print("SZ_DEPTH: %i" % SZ_DEPTH)
        print("SZ_RGB: %i" % SZ_RGB)
        print("SZ_OFFSET: %i" % SZ_OFFSET)
        print("SZ_TOTAL: %i" % (SZ_DEPTH + SZ_RGB + SZ_OFFSET))
        sys.stdout.flush()

        self.hfile = open(path_ram, "r+b")
        self.hram_depth = mmap.mmap(
            self.hfile.fileno(), offset=0, length=SZ_DEPTH, access=mmap.ACCESS_WRITE)
        self.hram_rgba = mmap.mmap(
            self.hfile.fileno(), offset=SZ_DEPTH + SZ_OFFSET, length=SZ_RGB, access=mmap.ACCESS_WRITE)
        self.hram_padding = SZ_OFFSET

    def __del__(self):
        print("Cleanup the files.")
        if self.hram_depth is not None:
            self.hram_depth.close()
        if self.hram_rgba is not None:
            self.hram_rgba.close()
        if self.hfile is not None:
            self.hfile.close()
            print("File closed.")


class BaseModuleCamera:
    def __init__(self, coms):
        self.coms = coms
        self.frame_depth = np.reshape(np.frombuffer(
            self.coms.hram_depth, dtype=np.float32), [HEIGHT, WIDTH])
        self.frame_rgba = np.reshape(np.frombuffer(
            self.coms.hram_rgba, dtype=np.uint8), [HEIGHT, WIDTH, 4])

    def queue_frame_data(self): raise Exception("Must be implemented in inhereting class!")


class ModuleWebcam(BaseModuleCamera):
    def __init__(self, coms, device_index, override_device=None):
        print("override_device:", override_device, flush=True)
        if override_device is None:
            self.capture = cv2.VideoCapture(device_index)
        else:
            print("use captured vide!!!!!!!!1", flush=True)
            self.capture = cv2.VideoCapture(override_device)

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

        super().__init__(coms)

    def __del__(self):
        self.capture.release()

    def queue_frame_data(self):
        ret, frame = self.capture.read()

        if not ret:
            raise Exception("Camera disconnected")

        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        self.frame_rgba[..., 0:3] = frame


class ModuleRealsense(BaseModuleCamera):
    def __init__(self, coms, override_device):
        self.pipeline, self.align = \
            self.init_realsense(override_device)
        super().__init__(coms)

    def __del__(self):
        self.pipeline.stop()

    def reset_realsense(self):
        self.pipeline.profile.get_device().hardware_reset()
        self.pipeline.stop()
        self.pipeline, self.align, (self.shared_buffer, self.input_frame) = self.__init_realsense(self.override_device) \
            if self.enable_rs \
            else (None, None, (None, None))

    def init_realsense(self, override_device=None):
        context = rs.context()
        devices = context.query_devices()

        print("Device count: %i" % len(devices))
        sys.stdout.flush()

        if len(devices) == 0 and override_device is None:
            raise NoDeviceException()

        pipeline = RSPipeLine(
            devices[0]
            if override_device is None
            else override_device
        )

        align_to = rs.stream.color
        align = rs.align(align_to)

        pipeline.start()

        return pipeline, align

    def queue_frame_data(self):
        pipeline, align = self.pipeline, self.align
        depth_scale = pipeline.depth_scale if pipeline is not None else 1

        frame = pipeline.wait_for_frames()
        frame = align.process(frame)

        color, depth = frame.get_color_frame(), frame.get_depth_frame()
        data_color = np.array(color.get_data(), dtype=np.uint8)
        data_depth = np.array(depth.get_data(), dtype=np.float32)

        self.frame_depth[...] = data_depth
        self.frame_rgba[..., 0:3] = data_color


async def main():
    global override_device

    sz_int = ctypes.sizeof(ctypes.c_int32)

    port, use_simple = struct.unpack("<2I", sys.stdin.buffer.read(sz_int * 2))
    cam_idx = struct.unpack("<i", sys.stdin.buffer.read(sz_int))[0]
    str_sock = "http://127.0.0.1:%i" % port
    rs = None

    if "override_device" not in globals():
        override_device = None

    if override_device is not None:
        use_simple = not override_device.endswith(".bag")

    path_ram = fetch_string(sys.stdin.buffer)

    print("Path RAM: '%s'" % path_ram)
    print("Socket string: '%s'" % str_sock)
    sys.stdout.flush()

    sock = socketio.AsyncClient()

    await sock.connect(str_sock)

    print("Socket connection established")
    sys.stdout.flush()

    await sock.emit("ipc_conn", {"type": "rs"})

    coms = ModuleComs(path_ram)

    @sock.event
    async def disconnect(): sys.exit(0)

    @sock.on("ipc_rs_cam")
    async def on_ipc_rs_cam(index):
        nonlocal rs
        print("Changing the camera to: %i" % index)
        cam_idx = index
        if rs is not None:
            del rs
            rs = None
        await sock.sleep(100 / 1000)
        rs = ModuleWebcam(coms, cam_idx)
        sys.stdout.flush()

    @sock.on("ipc_rs")
    async def on_ipc_rs():
        nonlocal rs
        global override_device
        sys.stdout.flush()
        while True:
            try:
                if use_simple:
                    print("Using simple model.")
                    sys.stdout.flush()
                    camera_list = await fetch_all_cameras()

                    if len(camera_list) == 0:
                        raise NoDeviceException()

                    print(camera_list)
                    sys.stdout.flush()

                    rs = ModuleWebcam(coms, camera_list[0]["camera_index"] if cam_idx < 0 else cam_idx, override_device)
                    await sock.emit("ipc_rs_resp", {
                        "ramPadding": rs.coms.hram_padding,
                        "dims": {"width": WIDTH, "height": HEIGHT},
                        "cameraList": camera_list,
                        "depthScale": 1,
                        "matrixK": [0] * 9
                    })
                else:
                    rs = ModuleRealsense(coms, override_device)
                    flat_K = np.reshape(rs.pipeline.matrix_K, [-1]).tolist()

                    await sock.emit("ipc_rs_resp", {
                        "ramPadding": rs.coms.hram_padding,
                        "dims": {"width": WIDTH, "height": HEIGHT},
                        "depthScale": rs.pipeline.depth_scale,
                        "matrixK": flat_K
                    })

                await sock.sleep(1)

                while True:
                    if rs is None:
                        break
                    rs.queue_frame_data()
                    await sock.sleep(100 / 1000)
            except Exception as ex:
                if isinstance(ex, NoDeviceException):
                    await sock.emit("ipc_rs_err", {"ex": "dev_none"})
                elif isinstance(ex, USB30Exception):
                    await sock.emit("ipc_rs_err", {"ex": "dev_usb"})
                elif isinstance(ex, DevInUseException):
                    await sock.emit("ipc_rs_err", {"ex": "dev_inuse"})

                sys.stderr.write("Exception caught: ")
                sys.stderr.write("'%s'\n" % str(ex))
                sys.stderr.flush()
                await sock.sleep(5)

    await sock.wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.CancelledError as ex:
        sys.stderr.write(str(ex))
        sys.stderr.flush()
        exit(0)

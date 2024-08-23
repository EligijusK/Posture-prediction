import os
import cv2
import sys
import mmap
import struct
import ctypes
import asyncio
import socketio
import aiohttp
import numpy as np
import importlib
from utils.fetch_string import fetch_string
from utils.fetch_cameras import fetch_all_cameras_async, fetch_all_cameras
from rs.exceptions import NoDeviceException, USB30Exception, DevInUseException

WIDTH, HEIGHT = 640, 480
# override_device = "/home/ratchet/Downloads/RS_D435I_20210428_175414.bag"
# override_device = "/home/ratchet/Downloads/Telegram Desktop/bandicam 2022-11-15 06-13-54-394.mp4"


class ModuleComs:
    def __init__(self, path_ram, path_ram_2):
        self.hram_depth = None
        self.hram_rgba = None
        self.hfile = None
        self.hfile2 = None

        SZ_DEPTH = WIDTH * HEIGHT * 1 * ctypes.sizeof(ctypes.c_float)
        SZ_RGB = WIDTH * HEIGHT * 4 * ctypes.sizeof(ctypes.c_uint8)
        SZ_OFFSET = mmap.ALLOCATIONGRANULARITY - SZ_DEPTH % mmap.ALLOCATIONGRANULARITY

        # initialize socket
        with open(path_ram, "wb") as f: # path_ram  FAILS TO WRITE TO PATH_RAM  /Users/eligijus/.sock
            f.write(np.zeros([HEIGHT, WIDTH], dtype=np.float32))
            f.write(b"\x00" * SZ_OFFSET)  # padding for wangblows
            # f.write(np.full([HEIGHT, WIDTH, 4], 255, dtype=np.uint8))

        with open(path_ram_2, "wb") as f2:
            f2.write(np.full([HEIGHT, WIDTH, 4], 255, dtype=np.uint8))

        print("SZ_DEPTH: %i" % SZ_DEPTH)
        print("SZ_RGB: %i" % SZ_RGB)
        print("SZ_OFFSET: %i" % SZ_OFFSET)
        print("SZ_TOTAL: %i" % (SZ_DEPTH + SZ_RGB + SZ_OFFSET))
        sys.stdout.flush()

        self.hfile = open(path_ram, "r+b") # path_ram /Users/eligijus/.sock
        self.hfile2 = open(path_ram_2, "r+b")  # path_ram /Users/eligijus/.sock
        self.hram_depth = mmap.mmap(
            self.hfile.fileno(), offset=0, length=SZ_DEPTH, access=mmap.ACCESS_WRITE)
        self.hram_rgba = mmap.mmap(
            self.hfile2.fileno(), offset=0, length=SZ_RGB, access=mmap.ACCESS_WRITE)
        self.hram_padding = SZ_OFFSET

    def __del__(self):
        # print("Cleanup the files.")
        if self.hram_depth is not None:
            self.hram_depth.close()
        if self.hram_rgba is not None:
            self.hram_rgba.close()
        if self.hfile is not None:
            self.hfile.close()
        if self.hfile2 is not None:
            self.hfile2.close()
            # print("File closed.")


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
        self.camera_count = 0
        self.camera_count_updating = 0
        self.local_index = 0
        self.disconnected_cameras = False
        self.disconnected_camera_index = []
        print("override_device:", override_device, flush=True)

        if override_device is None:
            print(device_index)
            self.capture = cv2.VideoCapture()
            print("Setup Video Capture Device", flush=True)
        else:
            print("use captured vide!!!!!!!!1", flush=True)
            self.capture = cv2.VideoCapture()

        self.capture.open(device_index, cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        print("Video Configuration", flush=True)
        sys.stdout.flush()
        super().__init__(coms)

    def __del__(self):
        self.capture.release()

    def queue_frame_data(self):
        if self.capture is not None and self.capture.isOpened():
            ret, frame = self.capture.read()

            if not ret:
                self.disconnected_cameras = True
                print("Camera disconnected")
                camera_list = fetch_all_cameras()
                print(camera_list)
                self.camera_count_updating = len(camera_list)
                sys.stdout.flush()
                self.capture.release()
                try:
                    # temp_capture = cv2.VideoCapture(1) # reikia trackinti visus indeksus jei kamera atsijungia bandyti prisijungti prie kazkurio is indeksu, kai pavyksta istrinti praeita open cv kintamaji ir ji perasyti reiskia reikia manidzinti ir indeksus pagal tai
                    # self.capture = cv2.VideoCapture(camera_list[0]["camera_index"])
                    index = self.local_index
                    if self.camera_count > 0:
                        print("camera count: " + str(self.camera_count))
                        sys.stdout.flush()
                        for count in range(self.camera_count):
                            if index >= self.camera_count:
                                index = 0
                            temp_capture = cv2.VideoCapture(index)
                            if temp_capture.isOpened():
                                if temp_capture.read()[0]:
                                    del self.capture
                                    self.capture = cv2.VideoCapture(index)
                                    ret, frame = self.capture.read()
                                    print("Camera connected! " + str(index))
                                    sys.stdout.flush()
                                    temp_capture.release()
                                    self.local_index = index
                                    del temp_capture
                                    break
                                else:
                                    if index not in self.disconnected_camera_index:
                                        self.disconnected_camera_index.append(index)
                                    temp_capture.release()
                            index += 1
                except Exception as ex:
                    print(ex)
                    sys.stdout.flush()

            if self.disconnected_cameras and self.camera_count == len(self.disconnected_camera_index):
                print("No camera found")
                sys.stdout.flush()

            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
            frame = cv2.resize(frame, (WIDTH, HEIGHT))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            self.frame_rgba[..., 0:3] = frame


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
    path_ram = path_ram.split(',')
    # print(path_ram[0])
    # print(path_ram[1])
    # path_ram = "/Users/eligijus/Desktop/Projektai/Posture-prediction/.sock"
    # print("Path RAM: '%s'" % path_ram)
    # print("Socket string: '%s'" % str_sock)
    # sys.stdout.flush()

    sock = socketio.AsyncClient()

    await sock.connect(str_sock)

    print("Socket connection established")
    sys.stdout.flush()

    await sock.emit("ipc_conn", {"type": "rs"})

    coms = ModuleComs(path_ram[0], path_ram[1])

    @sock.event
    async def disconnect(): sys.exit(0)

    @sock.on("ipc_rs_cam")
    async def on_ipc_rs_cam(index):
        nonlocal rs
        camera_list = await fetch_all_cameras_async()
        print(camera_list)

        camera_update_count = len(camera_list)
        if camera_update_count > rs.camera_count_updating:
            rs.camera_count_updating = camera_update_count
            await sock.emit("ipc_rs_new_camera", {"ex": "dev_none"})

        if rs.camera_count <= rs.local_index + 1:
            rs.local_index = 0
        else:
            rs.local_index += 1

        while rs.local_index in rs.disconnected_camera_index and rs.camera_count != len(rs.disconnected_camera_index):
            if rs.local_index >= rs.camera_count: # jei isjungiame vidurinia kamera paskutines kameros swicho metu nebepajungia
                rs.local_index = 0
            else:
                rs.local_index += 1
            print(rs.local_index)
            sys.stdout.flush()

        print(rs.disconnected_camera_index)
        # print(rs.local_index in rs.disconnected_camera_index and rs.camera_count != len(rs.disconnected_camera_index))
        # print(rs.local_index)
        sys.stdout.flush()

        rs.capture.release()
        rs.capture.open(rs.local_index, cv2.CAP_DSHOW) # if cam_idx < 0 else cam_idx
        # rs = ModuleWebcam(coms, cam_idx)
        # sys.stdout.flush()

    @sock.on("ipc_rs")
    async def on_ipc_rs():
        nonlocal rs
        global override_device
        # sys.stdout.flush()
        while True:
            try:
                if use_simple:
                    # print("Using simple model.")
                    # sys.stdout.flush()
                    camera_list = await fetch_all_cameras_async()
                    print(camera_list)

                    sys.stdout.flush()

                    # print("Using")
                    # sys.stdout.flush()

                    if len(camera_list) == 0:
                        raise NoDeviceException()

                    if rs is None:
                        rs = ModuleWebcam(coms, camera_list[0]["camera_index"]) #  if cam_idx < 0 else cam_idx, override_device
                    else:
                        rs.capture.release()
                        rs.capture.open(camera_list[0]["camera_index"], cv2.CAP_DSHOW) # if cam_idx < 0 else cam_idx

                    if rs.camera_count is not None and rs.camera_count == 0:
                        rs.camera_count = len(camera_list)
                        rs.camera_count_updating = len(camera_list)
                    # rs.capture.
                    # print("Opened?")
                    # sys.stdout.flush()

                    await sock.emit("ipc_rs_resp", {
                        "ramPadding": rs.coms.hram_padding,
                        "dims": {"width": WIDTH, "height": HEIGHT},
                        "cameraList": camera_list,
                        "depthScale": 1,
                        "matrixK": [0] * 9
                    })
                # print(camera_list)
                # sys.stdout.flush()

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

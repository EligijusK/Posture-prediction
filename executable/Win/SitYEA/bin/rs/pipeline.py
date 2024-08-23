import numpy as np
import pyrealsense2 as rs
import rs.config as cfg
from rs.exceptions import USB30Exception, DevInUseException

__align_to = rs.stream.color
__align = rs.align(__align_to)


class RSPipeLine:
    def __init__(self, dev):
        if type(dev) == str:
            self.from_file = dev
            self.framerate = 30
            self.name = dev
            self.serial_id = None
        else:
            self.from_file = None
            self.serial_id = dev.get_info(rs.camera_info.serial_number)
            self.name = dev.get_info(rs.camera_info.name).replace(
                "Intel RealSense", "RS").replace(" ", "_")
            self.framerate = 30 if self.name == "RS_L515" else 30

        self.pipeline = rs.pipeline()
        self.profile = None
        self.depth_scale = None
        self.matrix_K = None

    def get_config(self):
        return cfg.create_config(framerate=self.framerate, device_id=self.serial_id) \
            if self.from_file is None \
            else cfg.create_playback_config(self.from_file, framerate=self.framerate)

    def start(self, config=None):
        if self.profile is not None:
            raise DevInUseException()

        config = self.get_config() if config is None else config

        self.profile = self.pipeline.start(config)

        dev = self.profile.get_device()
        if self.from_file:
            self.serial_id = dev.get_info(rs.camera_info.serial_number)
            self.name = dev.get_info(rs.camera_info.name)

        # if int(dev.get_info(rs.camera_info.usb_type_descriptor)[0]) < 3:
        #     raise USB30Exception()

        depth_stream = self.profile.get_stream(rs.stream.depth)
        depth_sensor = dev.first_depth_sensor()

        self.depth_scale = depth_sensor.get_depth_scale()
        intrinsics = depth_stream.as_video_stream_profile().get_intrinsics()

        fx = float(intrinsics.fx)  # Focal length of x
        fy = float(intrinsics.fy)  # Focal length of y
        ppx = float(intrinsics.ppx)  # Principle Point Offsey of x (aka. cx)
        ppy = float(intrinsics.ppy)  # Principle Point Offsey of y (aka. cy)
        axs = 0.0  # Axis skew

        self.matrix_K = np.array([
            [fx, axs, ppx],
            [0.0, fy, ppy],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)

    def stop(self):
        if self.profile is None:
            return

        self.pipeline.stop()
        self.profile = None

    def wait_for_frames(self, timeout_ms=5000):
        return self.pipeline.wait_for_frames(timeout_ms=timeout_ms)

    def start_recording(self, dir, timestamp):
        path = "%s/%s_%s.bag" % (dir, self.name, timestamp)
        config = self.get_config()
        config.enable_record_to_file(path)

        self.start(config)

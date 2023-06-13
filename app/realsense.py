import cv2
import sys
import ctypes
import numpy as np
import mediapipe as mpipe
from time import time as now
import multiprocessing as mp
import configs.config as config
from PIL import Image as pilImage

HEIGHT, WIDTH, _ = config.DATA.RESOLUTION.FRAME

mp_drawing = mpipe.solutions.drawing_utils
mp_face = mpipe.solutions.face_detection
inf = 2 ** 31 - 1


class AppRealsense:
    def __init__(self, enable_rs, override_device=None):
        self.pipeline, self.align, (self.shared_buffer, self.input_frame) = self.__init_realsense(override_device) \
            if enable_rs \
            else (None, None, (None, None))

        self.depth_max = config.DATA.DEPTH.MAX
        self.faces = None

        self.enable_rs = enable_rs
        self.override_device = override_device

        self.poser = mp_face.FaceDetection(min_detection_confidence=0.5)
        self.calibration_heatmap = []
        self.bounds = np.array([int(x) for x in self.config.MODEL.CALIBRATION_BOUNDS.split(",")], dtype=np.int32)
        self.next_bad_notification = 0

    def __reset_realsense(self):
        self.pipeline.profile.get_device().hardware_reset()
        self.pipeline.stop()
        self.pipeline, self.align, (self.shared_buffer, self.input_frame) = self.__init_realsense(self.override_device) \
            if self.enable_rs \
            else (None, None, (None, None))

    def __init_realsense(self, override_device=None):
        import pyrealsense2 as rs
        from rs.config import create_config, create_playback_config
        from rs.pipeline import RSPipeLine

        context = rs.context()
        devices = context.query_devices()

        pipeline = RSPipeLine(
            devices[0] if override_device is None else override_device)

        align_to = rs.stream.color
        align = rs.align(align_to)

        pipeline.start()

        shared_arr = mp.Array(ctypes.c_float, HEIGHT * WIDTH * 4)
        input_frame = np.reshape(np.frombuffer(
            shared_arr.get_obj(), dtype=np.float32), [HEIGHT, WIDTH, 4])

        return pipeline, align, (shared_arr, input_frame)

    def __get_frame_data(self):
        input_frame = self.input_frame
        pipeline, align = self.pipeline, self.align
        depth_scale = pipeline.depth_scale if pipeline is not None else 1

        frame = pipeline.wait_for_frames()
        frame = align.process(frame)

        color, depth = frame.get_color_frame(), frame.get_depth_frame()
        data_color = np.array(color.get_data())
        data_depth = np.array(depth.get_data(), dtype=np.float32)

        input_frame[..., :3] = data_color / 255
        input_frame[..., 3] = data_depth

    def predict_face(self):
        input_frame = np.copy(self.input_frame)[..., :3]
        input_frame = np.array(input_frame * 255, dtype=np.uint8)

        h, w, _ = input_frame.shape
        faces = self.faces = self.poser.process(input_frame)# if np.random.random() > 0.1 else None

        if faces is not None and faces.detections is not None and len(faces.detections) > 0:
            face = faces.detections[0]
            nose = face.location_data.relative_keypoints[mp_face.FaceKeyPoint.NOSE_TIP]
        else:
            self.start_time = now()
            self._AppLabels__update_labels(
                                self.label_to_prediction("away"))

        return faces

    def check_calibration(self):
        left, top, right, bottom = self.bounds

        if left > right or top < bottom:
            return

        faces = self.faces
        h, w, _ = self.input_frame.shape

        if faces is not None and faces.detections is not None and len(faces.detections) > 0:
            face = faces.detections[0]
            nose = face.location_data.relative_keypoints[mp_face.FaceKeyPoint.NOSE_TIP]
            x, y = round(nose.x * w), round(nose.y * h)

            in_bounds = (x >= left) and (x <= right) and (y >= top) and (y <= bottom)
            bad_calibration = 60

            if in_bounds:
                self.next_bad_notification = now() + bad_calibration
            elif now() > self.next_bad_notification:
                self.notifications.calibration.send()
                self.next_bad_notification = now() + bad_calibration


    def __get_rs_frame(self, frame_size):
        has_rs = self.pipeline is not None

        if not has_rs:
            input_frame = pilImage.new("RGBA", (WIDTH, HEIGHT), "lightgray")
        else:
            input_frame = np.copy(self.input_frame)[..., :3]
            input_frame = np.array(input_frame * 255, dtype=np.uint8)

            if self.config.MODEL.CALIBRATION_ENABLED:
                if self.last_prediction[0] == "good":
                    faces = self.poser.process(input_frame)

                    if faces is not None and faces.detections is not None and len(faces.detections) > 0:
                        face = faces.detections[0]
                        nose = face.location_data.relative_keypoints[mp_face.FaceKeyPoint.NOSE_TIP]
                        x, y = nose.x, nose.y

                        self.calibration_heatmap.append([x, y])
                        self.calibration_heatmap = self.calibration_heatmap[-self.config.MODEL.CALIBRATION_HISTORY:]

                        csize = self.config.MODEL.CALIBRATION_SIZE
                        hsize = csize

                        self.bounds = [inf, inf, -inf, -inf]

                        h, w, _ = input_frame.shape
                        for x, y in self.calibration_heatmap:
                            x, y = round(x * w), round(y * h)
                            self.bounds[0] = min(self.bounds[0], x - hsize)
                            self.bounds[1] = min(self.bounds[1], y - hsize)
                            self.bounds[2] = max(self.bounds[2], x + hsize)
                            self.bounds[3] = max(self.bounds[3], y + hsize)

                input_frame = cv2.rectangle(
                    input_frame, self.bounds[0:2], self.bounds[2:4], (255, 0, 0))

            input_frame = cv2.merge(
                [input_frame, np.full([HEIGHT, WIDTH], 255, dtype=np.uint8)])

            input_frame = pilImage.fromarray(input_frame)

        return self._AppFrame__get_framed(input_frame, frame_size)

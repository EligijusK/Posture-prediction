import imp
import time
import atexit
import numpy as np
from scipy.stats import mode
import multiprocessing as mp
from time import time as now
import configs.config as config
from utils.image_to_points import image_to_points

HEIGHT, WIDTH, _ = config.DATA.RESOLUTION.FRAME

mp.set_start_method('spawn', True)


def start_deferred_process(shared_buffer, label_count, load_model, path_model, path_checkpoint, matrix_K, depth_scale, depth_max, pipe):
    class AppModelDeferred:
        def __init__(self, shared_buffer, label_count, load_model, path_model, path_checkpoint, matrix_K, depth_scale, depth_max):
            self.shared_buffer = shared_buffer
            self.matrix_K = matrix_K
            self.depth_scale = depth_scale
            self.depth_max = depth_max
            self.label_count = label_count

            self.network, self.create_tensor = self.__load_model(path_model, path_checkpoint) \
                if load_model \
                else (None, None)

        def __load_model(self, path_model, path_checkpoint):
            import os
            import sys
            from torch import cuda, tensor

            try:
                device = "cpu"
                if cuda.is_available():
                    x = tensor([0.0], device="cuda")

                    if "cuda" in x.device.type:
                        device = "cuda"
            except:
                device = "cpu"

            if not getattr(sys, "frozen", False):
                py_path = "%s/__init__.py" % path_model
                pyc_path = "%s/__init__.pyc" % path_model

                py_path = pyc_path if os.path.exists(pyc_path) else py_path
                print("Loading network: %s" % py_path)
                module_model = imp.load_package("_network", py_path)
            else:
                import model as module_model

            network = module_model.StrippedNetwork(
                label_count=self.label_count,
                path_weights=path_checkpoint,
                device="cpu"
                # device="cuda" if cuda.is_available() else "cpu"
            )

            return network, tensor

        def get_prediction(self):
            matrix_K = self.matrix_K
            depth_scale = self.depth_scale
            depth_max = self.depth_max

            input_frame = np.reshape(np.frombuffer(
                self.shared_buffer.get_obj(), dtype=np.float32), [HEIGHT, WIDTH, 4])
            input_frame = np.copy(input_frame)

            input_frame = image_to_points(
                input_frame, matrix_K, depth_scale, depth_max)

            tensor = self.create_tensor(
                np.array([input_frame]), device=self.network.device)
            prediction = self.network.predict(tensor).cpu().numpy()

            return prediction[0]

    app = AppModelDeferred(shared_buffer, label_count, load_model, path_model,
                           path_checkpoint, matrix_K, depth_scale, depth_max)

    pipe.send("ready")

    while True:
        pipe.recv()
        pipe.send(app.get_prediction())
        time.sleep(0.01)


class AppModel:
    def __init__(self, shared_buffer, load_model, path_model, path_checkpoint):
        self.last_prediction = ("unknown", now(), "unknown", now())

        if not self.pipeline or not load_model:
            self.has_tf = False
            return

        self.has_tf = True
        parent_conn, child_conn = mp.Pipe()

        self.pipe = parent_conn

        self.proc = mp.Process(target=start_deferred_process, args=(
            shared_buffer,
            len(self.man_labels.get_shape()),
            load_model,
            path_model,
            path_checkpoint,
            self.pipeline.matrix_K,
            self.pipeline.depth_scale,
            self.depth_max,
            child_conn,
        ))

        self.proc.start()

        while not self.pipe.poll(0.01):
            self.pipe.recv()
            break

        self.pipe.send("ready")
        self.polled = True
        self.next_time = now() + self.config.HISTORY.TIME_PREDICTION

        atexit.register(self.__at_exit)

    def __at_exit(self):
        self.proc.kill()
        self.proc = None

    def __try_poll(self):
        if self.polled or self.proc is None:
            return

        self.pipe.send("ready")
        self.polled = True

    def __is_ready(self): return now() > self.next_time

    def __get_prediction(self):
        faces = self.faces
        last_frames = self.last_frames

        if faces is None or faces.detections is None or len(faces.detections) == 0:
            pred_label = "empty"
            last_frames.append(pred_label)
            self.last_frames = last_frames = last_frames[-self.max_frames:]
        elif self.pipe.poll(0.01):
            prediction = self.pipe.recv()
            pred_label, _, _ = self.man_labels.get_label(prediction)
            last_frames.append(pred_label)

            self.last_frames = last_frames = last_frames[-self.max_frames:]
            self.polled = False

        pred_label = mode(last_frames).mode[0]

        colors = self.color_cache[pred_label]
        color_text, color_rect = colors.colorRect, colors.colorText

        self.next_time = now() + self.config.HISTORY.TIME_PREDICTION

        return pred_label, color_text, color_rect

import os
import imp
import sys
import mmap
import time
import struct
import ctypes
import asyncio
import socketio
import numpy as np
import mediapipe as mpipe
import utils.math as mathutils
from collections import Counter
import utils.mediapipe as mputils
from utils.skeleton import Skeleton
from utils.get_asset import get_asset_path
from utils.fetch_string import fetch_string
from data.label_manager import LabelManager
from torch import cuda, tensor as create_tensor
from utils.image_to_points import image_to_points

PATH_TAXONOMY = get_asset_path("data/label_hierarchy.json")

mp_drawing = mpipe.solutions.drawing_utils
mp_face = mpipe.solutions.face_detection
mp_pose = mpipe.solutions.pose
inf = 2 ** 31 - 1

PRED_NONE = "none"
PRED_GOOD = "good"
PRED_POOR = "poor"
PRED_GRIM = "grim"

def mode(arr):
    c = Counter(arr)
    return c.most_common(1)[0][0]


class ModulePred:
    def __init__(self, *, use_gpu, use_simple, ram_padding, path_ram, man_labels, width, height,
                 depth_scale, matrix_K, path_model, path_checkpoint, depth_max, max_frames):

        SZ_DEPTH = width * height * 1 * ctypes.sizeof(ctypes.c_float)
        SZ_RGB = width * height * 4 * ctypes.sizeof(ctypes.c_uint8)

        self.width = width
        self.height = height
        self.depth_scale = depth_scale
        self.matrix_K = matrix_K
        self.man_labels = man_labels
        self.depth_max = depth_max
        self.max_frames = max_frames
        self.use_simple = use_simple

        if not use_simple:
            print("Loading model...")
            sys.stdout.flush()
            self.network = self.load_model(
                use_gpu, len(man_labels.get_shape()),
                path_model, path_checkpoint
            )
            self.facer = mp_face.FaceDetection(min_detection_confidence=0.5)
        else:
            print("Loading model...")
            sys.stdout.flush()
            self.network = self.load_model(
                use_gpu, len(man_labels.get_shape()),
                path_model, path_checkpoint
            )
            print("Using mediapipe predictions.")
            self.poser = mp_pose.Pose(min_detection_confidence=0.7)
            self.skeleton = Skeleton()

            def create_gaussian_kernel(size, sigma):
                mean = size * 0.5

                def gaussian_formula(x):
                    return np.exp(-0.5 * (np.power((x - mean) / sigma, 2.0))) \
                        / (2 * np.pi * sigma * sigma)

                kernel = np.array([gaussian_formula(x) for x in range(size)])

                return np.reshape(kernel / np.sum(kernel), [size, 1, 1])

            self.kernel = create_gaussian_kernel(self.max_frames, 1)
            self.skeleton_history = np.zeros([self.max_frames, 33, 3])
            self.first_frame = False

        print("Opening RAM file...")
        sys.stdout.flush()

        self.hfile = open(path_ram, "r")

        print("RAM open. Remapping...")
        sys.stdout.flush()

        self.hram_depth = mmap.mmap(
            self.hfile.fileno(), offset=0, length=SZ_DEPTH, access=mmap.ACCESS_READ)
        self.hram_rgba = mmap.mmap(
            self.hfile.fileno(), offset=SZ_DEPTH + ram_padding, length=SZ_RGB, access=mmap.ACCESS_READ)

        print("RAM remapped.")
        sys.stdout.flush()

        self.frame_depth = np.reshape(np.frombuffer(
            self.hram_depth, dtype=np.float32), [height, width])
        self.frame_rgba = np.reshape(np.frombuffer(
            self.hram_rgba, dtype=np.uint8), [height, width, 4])

        self.placeholder = np.empty([height, width, 4], dtype=np.float32)
        self.last_frames = ["empty"]

        print("Model is initialized.")
        sys.stdout.flush()

    def load_model(self, use_gpu, label_count, path_model, path_checkpoint):
        try:
            device = "cpu"
            if use_gpu and cuda.is_available():
                x = create_tensor([0.0], device="cuda")

                if "cuda" in x.device.type:
                    device = "cuda"
        except:
            device = "cpu"

        print("Use device for network: %s" % device)
        sys.stdout.flush()

        if not getattr(sys, "frozen", False):
            py_path = "%s/__init__.py" % path_model
            pyc_path = "%s/__init__.pyc" % path_model

            py_path = pyc_path if os.path.exists(pyc_path) else py_path
            print("Loading network: %s" % py_path)
            sys.stdout.flush()
            module_model = imp.load_package("_network", py_path)
        else:
            if self.use_simple:
                import model_simple as module_model
            else:
                import model_full as module_model

        return module_model.StrippedNetwork(
            label_count=label_count,
            path_weights=path_checkpoint,
            device=device
        )

    def __del__(self):
        self.hram_depth.close()
        self.hram_rgba.close()
        self.hfile.close()

    def predict_net(self):
        rgb = np.copy(self.frame_rgba[..., 0:3])
        depth = np.copy(self.frame_depth)[..., np.newaxis]
        faces = self.facer.process(rgb)

        if faces is None or faces.detections is None or len(faces.detections) == 0:
            pred_label, nose = "empty", None
        else:
            rgbd = np.concatenate([rgb / 255, depth], -1, self.placeholder)
            pc = image_to_points(rgbd, self.matrix_K,
                                 self.depth_scale, self.depth_max)

            tensor = create_tensor(np.array([pc]), device=self.network.device)
            prediction = self.network.predict(tensor).cpu().numpy()[0]

            pred_label, _, _ = self.man_labels.get_label(prediction)

            face = faces.detections[0]
            nose = face.location_data.relative_keypoints[mp_face.FaceKeyPoint.NOSE_TIP]
            nose = {"x": nose.x, "y": nose.y}

        return pred_label, nose, None

    def predict_mp(self):
        rgb = np.copy(self.frame_rgba[..., 0:3])
        posed = self.poser.process(rgb)
        skeleton = self.skeleton

        if posed.pose_landmarks is None:
            pred_label, nose = "empty", None
            pose = None
        else:
            landmarks = mputils.landmarks2numpy(
                posed.pose_landmarks.landmark)[..., 0:3]

            self.skeleton_history[:-1] = self.skeleton_history[1:]
            self.skeleton_history[-1] = landmarks
            if self.first_frame:
                for i in range(self.max_frames - 1):
                    self.skeleton_history[i] = landmarks
                self.first_frame = True

            avg_skeleton = np.sum(self.skeleton_history * self.kernel, axis=0)

            tensor = create_tensor(
                np.array([avg_skeleton]), device=self.network.device)
            prediction = self.network.predict(tensor).cpu().numpy()[0]

            pred_label, _, _ = self.man_labels.get_label(prediction)
            b = (skeleton.HEAD_LEFT + skeleton.HEAD_RIGHT) * 0.5

            skeleton.update(avg_skeleton)
            pose = skeleton.fetch_pose(self.width, self.height)

            if pred_label != "sitting straight":
                ref1 = (skeleton.HEAD_LEFT[0:2] +
                        skeleton.HEAD_RIGHT[0:2]) * 0.5
                ref2 = (skeleton.SHOULDER_LEFT[0:2] +
                        skeleton.SHOULDER_RIGHT[0:2]) * 0.5

                ref = np.sum((ref2 - ref1) ** 2) ** 0.5

                len1 = np.linalg.norm(skeleton.HEAD_LEFT - skeleton.HEAD_RIGHT)
                len2 = np.linalg.norm(
                    skeleton.SHOULDER_LEFT - skeleton.SHOULDER_RIGHT)
                ratio = len2 / len1

                # print("%s -> %f" % (pred_label, ratio), flush=True)
                if ratio >= 2.35 and ratio <= 2.6:
                    pred_label = "sitting straight"

            nose = {"x": float(b[0]), "y": float(b[1])}

        return pred_label, nose, pose

    def predict(self):

        pred_label, nose, pose = self.predict_mp(
        ) if self.use_simple else self.predict_net()

        self.last_frames.append(pred_label)
        self.last_frames = self.last_frames[-self.max_frames:]

        true_label = mode(self.last_frames)

        if true_label == "empty" or true_label == "unknown":
            return PRED_NONE, true_label, self.last_frames, nose, pose
        elif true_label == "sitting straight":
            return PRED_GOOD, true_label, self.last_frames, nose, pose
        elif true_label == "lightly hunching" or true_label == "partially lying":
            return PRED_POOR, true_label, self.last_frames, nose, pose

        return PRED_GRIM, true_label, self.last_frames, nose, pose


async def main():
    print("Proc MDL started.")
    sys.stdout.flush()

    sz_int = ctypes.sizeof(ctypes.c_int32)
    sz_float = ctypes.sizeof(ctypes.c_float)

    port, ram_padding, use_gpu, use_simple, width, height, max_frames = struct.unpack(
        "<7I", sys.stdin.buffer.read(sz_int * 7))

    print(port, ram_padding, use_gpu, use_simple, width, height, max_frames)
    sys.stdout.flush()

    depth_scale, depth_max = struct.unpack(
        "<2f", sys.stdin.buffer.read(sz_float * 2))
    matrix_K = struct.unpack("<9f", sys.stdin.buffer.read(sz_float * 9))

    path_ram = fetch_string(sys.stdin.buffer)
    path_model = "%s_%s" % (fetch_string(sys.stdin.buffer),
                            "simple" if use_simple else "full")
    path_checkpoint = "%s/model.xth" % path_model
    str_sock = "http://127.0.0.1:%i" % port

    print("Path RAM: '%s'" % path_model)
    print("Path model: '%s'" % path_model)
    print("Path checkpoint: '%s'" % path_checkpoint)
    print("Socket string: '%s'" % str_sock)
    sys.stdout.flush()

    sock = socketio.AsyncClient()

    await sock.connect(str_sock)

    print("Socket connection established")
    sys.stdout.flush()

    await sock.emit("ipc_conn", {"type": "mdl"})

    man_labels = LabelManager(PATH_TAXONOMY, False)
    pred = ModulePred(
        man_labels=man_labels,
        width=width,
        height=height,
        depth_scale=depth_scale,
        depth_max=depth_max,
        matrix_K=np.reshape(matrix_K, [3, 3]),
        path_ram=path_ram,
        path_model=path_model,
        path_checkpoint=path_checkpoint,
        max_frames=max_frames,
        ram_padding=ram_padding,
        use_gpu=use_gpu != 0,
        use_simple=use_simple != 0
    )

    @sock.on("ipc_mdl")
    async def on_ipc_mdl(args):
        pred.max_frames = args["prediction_frames"]

        label, true_label, last_frames, face, pose = pred.predict()

        await sock.emit("ipc_mdl_resp", {
            "label": label,
            "face": face,
            "pose": pose,
            "true_label": true_label,
            "last_frames": last_frames
        })
        await sock.sleep(0.1)

    @sock.event
    async def disconnect(): exit(0)

    await sock.wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.CancelledError as ex:
        sys.stderr.write(str(ex))
        sys.stderr.flush()
        exit(0)

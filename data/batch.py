import numpy as np
import cv2
import configs.config as cfg
from math import ceil
from utils.exr import read_exr
from utils.math import depth_to_cloud
from configs.args import args
from tqdm import tqdm
from torch.utils.data import Dataset
from data.label_manager import LabelManager
from scipy.sparse import coo_matrix

_h, _w, _ch = cfg.DATA.RESOLUTION.FRAME


class Batch(Dataset):
    def __init__(self, *, elements, depth_max, augment, man_labels: LabelManager):
        count_elements = len(elements)
        elements = elements
        elements = np.array(elements)

        self.array_cache, self.array_length, self.label_map, _ = man_labels.label_cache
        self.deta = 0.01
        self.uniform_distribution = np.full(
            self.array_length, 1.0 / self.array_length, dtype=np.float32)
        self.path_map = {}

        for element in elements:
            self.path_map[element.frame_path] = element

        self.count_elements = count_elements
        self.elements = elements

        self.depth_max = depth_max
        self.should_augment = augment

        self.iterator = 0
        self.iterations = self.count_elements

    def __iter__(self): return self

    def read_exr(self, path, matrix_K, depth_scale):
        _fx, _fy = matrix_K[0, 0], matrix_K[1, 1]
        _cx, _cy = matrix_K[0, 2], matrix_K[1, 2]

        frame = read_exr(path, "RGBZ")

        depth = frame[..., 3] = frame[..., 3] * depth_scale
        mask = depth > self.depth_max
        frame[mask] = 0

        point_cloud = depth_to_cloud(
            _w, _h, _fx, _fy, _cx, _cy, frame, dtype=np.float32)

        return np.reshape(point_cloud, [-1, 6])

    def __getitem__(self, index):
        element = self.elements[index]

        if not cfg.TRAINING.USE_PREPROCESSED:
            inputs = self.read_exr(
                element.frame_path, element.intrinsics, element.depth_scale)

            onehot = self.array_cache[element.labels]
            outputs = onehot * (1 - self.deta) + self.deta * \
                self.uniform_distribution
        else:
            file_path = element.frame_path.replace(
                ".exr", "_%i.npy" % cfg.MODEL.IN_POINTS)

            with open(file_path, "rb") as f:
                inputs, outputs = np.load(f, allow_pickle=True)

        if self.should_augment:
            randomized = [np.random.uniform() for x in range(6)]
            inputs = self.augment(inputs, randomized)

        inputs = inputs[inputs[:, 5] > 0]
        # inputs = coo_matrix(inputs)

        return element, inputs, outputs

    def augment(self, inputs, randomized):
        r_fip_h, r_hue, r_sat, r_hue_val, r_hue_sat, r_no_light = randomized

        randomize_hue = r_hue < 0.25
        randomize_saturation = r_sat < 0.25
        disable_light = r_no_light < 0.5
        flip_h = r_fip_h < 0.25

        if flip_h:
            inputs[..., 4] = -inputs[..., 4]

        if disable_light:
            inputs[:, 0:3] = 0
        elif randomize_hue or randomize_saturation:
            color_map = inputs[np.newaxis, :, 0:3]
            color_map = cv2.cvtColor(color_map, cv2.COLOR_RGB2HSV)

            random_hue = 0.5 - r_hue_val
            random_saturation = 0.5 - r_hue_sat

            if randomize_hue:
                color_map[..., 0] *= 1 - random_hue
            if randomize_saturation:
                color_map[..., 1] *= 1 - random_saturation

            inputs[:, 0:3] = cv2.cvtColor(color_map, cv2.COLOR_HSV2RGB)[0]

        return inputs

    def __next__(self):

        if self.iterator >= self.count_elements:
            raise StopIteration

        items= self.__getitem__(self.iterator)
        self.iterator= self.iterator + 1

        return items

    def __len__(self):
        return self.iterations

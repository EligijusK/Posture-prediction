import re as _re
import os as _os
import numpy as _np
from tqdm import tqdm as _tqdm
from easydict import EasyDict as _EasyDict
from utils.files import load_json as _load_json
from math import ceil as _ceil
import configs.config as cfg

regexp = _re.compile("^(\d+_\d+)\/view_(\d+)\.exr$")


def get_directories(dir_root):
    dirpath, dirnames, filenames = next(_os.walk(dir_root))

    return ["%s/%s" % (dirpath, dir) for dir in dirnames], dirnames


def consume_dirs(in_all_dirs, grouped_frames):
    total_frames = 0
    for dir_path in _tqdm(in_all_dirs):
        path_valid_frames = "%s/valid_bag_frame_list.json" % dir_path

        if not _os.path.exists(path_valid_frames):
            continue

        for frame in _load_json(path_valid_frames):
            label = frame["labels"]

            if label not in grouped_frames:
                grouped_frames[label] = []

            frame_path = frame["path"]

            frame_dir, frame_id = regexp.search(frame_path) \
                .groups()
            frame_id = int(frame_id)

            frame_dir = "%s/%s" % (cfg.DATA.INPUTS, frame_dir)
            sensor_data = _load_json("%s/sensor_info.json" % frame_dir)

            frame = _EasyDict(frame)
            frame.frame_dir = frame_dir
            frame.frame_id = frame_id
            frame.frame_path = "%s/%s" % (cfg.DATA.INPUTS, frame_path)
            frame.depth_scale = sensor_data.scale
            frame.intrinsics = _np.reshape(sensor_data.intrinsics, [3, 3])

            grouped_frames[label].append(frame)
            total_frames += 1

    return total_frames


def get_dataset(dir_input, training_ratio, reduced_dataset):
    all_dirs, _ = get_directories(dir_input)
    all_dirs = _np.random.permutation(
        all_dirs[0:min(reduced_dataset, len(all_dirs))])
    total_dirs = len(all_dirs)

    validation_elements = max(1, total_dirs - _ceil(total_dirs * training_ratio)) \
        if training_ratio < 1 \
        else 0

    if validation_elements > 0:
        all_dirs_training, all_dirs_validation = all_dirs[:-
                                                          validation_elements], all_dirs[-validation_elements:]
    else:
        all_dirs_training, all_dirs_validation = all_dirs, []

    grouped_frames_training, grouped_frames_validation, total_frames = {}, {}, 0

    total_frames += consume_dirs(all_dirs_training,
                                 grouped_frames_training)
    total_frames += consume_dirs(all_dirs_validation,
                                 grouped_frames_validation)

    training_elements, testing_elements = [], []

    print("-----------------------------------")
    print("All objects")
    print("-----------------------------------")
    for key in grouped_frames_training:
        frame_count_training = len(
            grouped_frames_training[key])
        frame_count_validation = (
            len(grouped_frames_validation[key]) if key in grouped_frames_validation else 0)

        frame_count = frame_count_training + frame_count_validation

        ratio = frame_count / total_frames * 100

        all_frames_training = _np.random.permutation(
            grouped_frames_training[key])

        all_frames_validation = grouped_frames_validation[key] \
            if key in grouped_frames_validation \
            else []

        training_elements = _np.concatenate(
            [training_elements, all_frames_training])
        testing_elements = _np.concatenate(
            [testing_elements, all_frames_validation])

        print("'%s'\twith %i (%i) frames (%.2f%%)" %
              (key, frame_count, frame_count_validation, ratio))
    print("-----------------------------------")

    return training_elements, testing_elements

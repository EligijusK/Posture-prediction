import os
import torch
import torch.nn as nn
import numpy as np
from tqdm import tqdm
from network.models.point_gather import PointGatherColored
from data.dataset import Dataset
from data.label_manager import LabelManager
import configs.config as cfg

dataset = Dataset(
    dir_input=cfg.DATA.INPUTS,
    training_ratio=1,
    augment=cfg.TRAINING.AUGMENT,
    depth_max=cfg.DATA.DEPTH.MAX,
    man_labels=LabelManager(cfg.DATA.PATH_TAXONOMY)
)

data, _ = dataset.gen_batches(32, num_workers=12)

samplers = [PointGatherColored(2 ** x) for x in range(11, 14)]

for b_path, b_inputs, b_outputs in tqdm(iter(data)):

    samples = [[sampler.samples, sampler(
        b_inputs.cuda()).detach().cpu().numpy()] for sampler in samplers]

    for count, sampled in samples:
        for path, sample, output in zip(b_path, sampled, b_outputs.numpy()):
            out_path = path.replace(".exr", "_%i.npy" % count)

            if not os.path.exists(out_path):
                with open(out_path, "wb") as f:
                    np.save(f, np.array([sample, output]))

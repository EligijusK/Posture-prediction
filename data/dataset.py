import os
from utils.files import load_json
from math import ceil
import configs.config as cfg
from easydict import EasyDict
from data.batch import Batch
from configs.args import args
from utils.math import reseed_rng
from data.get_dataset import get_dataset
import numpy as np
from torch.utils.data import DataLoader


class Dataset:
    def __init__(self, *, dir_input, training_ratio, augment, depth_max, man_labels):
        reseed_rng(1337)

        self.training, self.testing = Dataset.get_dataset(
            dir_input=dir_input,
            training_ratio=training_ratio
        )

        self.count_training = len(self.training)
        self.count_testing = len(self.testing)

        self.augment = augment
        self.depth_max = depth_max
        self.man_labels = man_labels

    def gen_batches(self, batch_size, test_batch_size=None, num_workers=0, use_cache=True, shuffle_train=True, drop_last=True):
        prefetch_factor = 5 if num_workers > 0 else 2
        persistent_workers = True if num_workers > 0 else False

        training_batch = DataLoader(
            Batch(
                elements=self.training,
                augment=self.augment,
                depth_max=self.depth_max,
                man_labels=self.man_labels
            ),
            batch_size=batch_size,
            num_workers=num_workers,
            drop_last=drop_last,
            shuffle=shuffle_train,
            prefetch_factor=prefetch_factor,
            persistent_workers=persistent_workers
        )

        testing_batch = DataLoader(
            Batch(
                elements=self.testing,
                augment=False,
                depth_max=self.depth_max,
                man_labels=self.man_labels
            ),
            batch_size=batch_size if test_batch_size is None else test_batch_size,
            num_workers=num_workers,
            drop_last=drop_last,
            prefetch_factor=prefetch_factor,
            persistent_workers=persistent_workers
        )

        return training_batch, testing_batch

    @staticmethod
    def get_dataset(*, dir_input, training_ratio):
        return get_dataset(
            dir_input=dir_input,
            training_ratio=training_ratio,
            reduced_dataset=args.reduced_dataset
        )

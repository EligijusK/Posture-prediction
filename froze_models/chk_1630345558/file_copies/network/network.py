import os
import re
import imp
import torch
import shutil
import atexit
import numpy as np
import configs.config as cfg
from configs.args import args
from utils.sys_colors import GREEN, RESET
from network.scaled_optimizer import ScaledOptimizer
import torch.utils.tensorboard as tensorboard
from network.state import create_empty_state, set_state, copy_state
from time import time as get_time
from network.models import Model
from data.label_manager import LabelManager
from data.dataset import Dataset
from utils.files import load_json, save_json, copy_file


class Network:
    def __init__(self, *, checkpoint: str = None, checkpoint_type: str = None, man_labels: LabelManager):
        if checkpoint == "latest":
            checkpoint = self.find_last_checkpoint()
            print("%sUsing latest checkpoint, found: '%s'%s" %
                  (GREEN, checkpoint, RESET))

        self.settings = {
            "learning_rate": args.learning_rate
        }

        self.man_labels = man_labels
        self.checkpoint = round(get_time()) if not checkpoint else checkpoint
        self.net: Model = self.ModelConstructor(
            in_points=cfg.MODEL.IN_POINTS,
            use_preprocessed=cfg.TRAINING.USE_PREPROCESSED,
            label_count=len(man_labels.get_shape())
        )
        self.current_state = create_empty_state()
        self.optimizer = ScaledOptimizer(
            learning_rate=args.learning_rate,
            mixed_precision=args.mixed_precision
        )

        # self.net.compile(self.optimizer)

        if checkpoint:
            self.restore(checkpoint_type=checkpoint_type)

    @staticmethod
    def get_dir_save(checkpoint: str) -> str:
        return "%s/chk_%s" % (cfg.TRAINING.OUTPUT_MODELS, checkpoint)

    @property
    def dir_save(self) -> str:
        return Network.get_dir_save(self.checkpoint)

    @property
    def ModelConstructor(self) -> Model:
        py_path = py_path = "%s/file_copies/network/models/__init__.py" % self.dir_save

        if os.path.isfile(py_path):
            module_model = imp.load_package("_models", py_path)

            return module_model.Model
        else:
            return Model

    def cleanup(self):
        if self.current_state.last_state.epoch == 0:
            shutil.rmtree(self.dir_save)

    def find_last_checkpoint(self) -> str:
        _, dirs_checkpoints, _ = next(os.walk(cfg.TRAINING.OUTPUT_MODELS))

        last_checkpoint, last_time = None, 0

        regexp = re.compile("^chk_(?P<checkpoint>\d+)$")

        for dir_checkpoint_name in dirs_checkpoints:
            matches = regexp.match(dir_checkpoint_name)

            if matches is None:
                continue

            dir_checkpoint = "%s/%s" % (cfg.TRAINING.OUTPUT_MODELS,
                                        dir_checkpoint_name)

            time = os.path.getmtime(dir_checkpoint)

            if last_time < time:
                last_checkpoint = int(matches.groupdict()["checkpoint"])
                last_time = time

        return last_checkpoint

    def predict(self, inputs: np.array) -> np.array:
        return self.net.predict(inputs)

    def restore(self, checkpoint_type):
        dir_save = self.dir_save

        json_path = "%s/model_info.json" % dir_save

        if os.path.exists(json_path):
            model_info = load_json(json_path)

            if checkpoint_type == "model":
                self.current_state = model_info
            elif checkpoint_type == "model_best_train" or checkpoint_type == "model_best_test":
                cur_state = model_info.last_state

                if checkpoint_type == "model_best_train":
                    best_state = model_info.best_state.train
                else:
                    best_state = model_info.best_state.test

                cur_state.epoch = best_state.epoch
                copy_state(cur_state.train, best_state.train)
                copy_state(cur_state.test, best_state.test)

                self.current_state = model_info
            else:
                raise Exception(
                    "Invalid checkpoint type: %s" % checkpoint_type)

        path = "%s/%s.pth" % (dir_save, checkpoint_type)

        if os.path.exists(path):
            self.net.restore(path, args.load_optimizer)

    @staticmethod
    def copy_file(src, dst):
        if not os.path.exists(dst):
            shutil.copy(src, dst)

    def train(self, *, dataset: Dataset):
        model = self.net
        net_model = self.net.model
        optimizer = self.optimizer

        dir_save = self.dir_save
        dir_save_cpy = "%s/file_copies" % dir_save
        dir_save_cpy_network = "%s/network" % dir_save_cpy
        dir_save_cpy_models = "%s/models" % dir_save_cpy_network

        last_state = self.current_state.last_state
        best_state = self.current_state.best_state
        best_train, best_test = last_state.train.loss, last_state.test.loss

        os.makedirs(dir_save, exist_ok=True)
        os.makedirs(dir_save_cpy, exist_ok=True)
        os.makedirs(dir_save_cpy_network, exist_ok=True)
        os.makedirs(dir_save_cpy_models, exist_ok=True)
        base_dir = cfg.BASE_DIR

        Network.copy_file(
            "%s/network/network.py" % base_dir,
            "%s/network.py" % dir_save_cpy_network
        )

        Network.copy_file(
            "%s/network/stripped_network.py" % base_dir,
            "%s/stripped_network.py" % dir_save_cpy_network
        )

        Network.copy_file(
            "%s/network/__init__.py" % base_dir,
            "%s/__init__.py" % dir_save_cpy_network
        )

        dir_network = "%s/network/models" % base_dir
        _, _, files = next(os.walk(dir_network))

        for path_model in files:
            Network.copy_file(
                "%s/%s" % (dir_network, path_model),
                "%s/%s" % (dir_save_cpy_models, path_model)
            )

        summary_training, summary_testing = [
            tensorboard.SummaryWriter(log_dir="%s/logs_%s" % (dir_save, p))
            for p in ["training", "testing"]
        ]

        atexit.register(self.cleanup)

        path_latest = "%s/model" % dir_save
        path_best_test = "%s/model_best_test" % dir_save
        path_best_train = "%s/model_best_train" % dir_save
        path_model_info = "%s/model_info.json" % dir_save

        data_train, data_testing = dataset.gen_batches(
            args.batch_size,
            num_workers=args.workers
        )

        save_json("%s/settings.json" % dir_save, self.settings)

        def do_epoch(epoch):
            nonlocal best_train, best_train, best_test

            learning_rate = self.optimizer.learning_rate
            print("%s---------------------------------------\n%sEpoch: %i (LR: %.8E)" %
                  (GREEN, RESET, epoch + 1, learning_rate))

            result = model.fit(data_train)

            train_total = result["history"][0]
            train_loss_total = train_total["loss"]["loss"]
            train_acc_total = train_total["accuracy"]["acc"]

            last_state.epoch = epoch + 1
            set_state(last_state.train, train_loss_total)

            if epoch >= args.testing_set:
                test_total = model.evaluate(data_testing)
                test_loss_total = test_total["loss"]["loss"]
                test_acc_total = test_total["accuracy"]["acc"]

                set_state(last_state.test, test_loss_total)

            with summary_training as writer:
                writer.add_scalar("loss", train_loss_total, epoch)
                writer.add_scalar("accuracy", train_acc_total, epoch)
                writer.add_scalar("learning_rate", learning_rate, epoch)

            if epoch >= args.testing_set:
                with summary_testing as writer:
                    writer.add_scalar("loss", test_loss_total, epoch)
                    writer.add_scalar("accuracy", test_acc_total, epoch)
                    writer.add_scalar("learning_rate", learning_rate, epoch)

            model.save_weights("%s.pth" % path_latest)

            if best_train > train_loss_total:
                best_train = train_loss_total

                best_state.train.epoch = epoch + 1
                set_state(best_state.train.train, train_loss_total)

                if epoch >= args.testing_set:
                    set_state(best_state.train.test, test_loss_total)

                copy_file("%s.pth" % path_latest, "%s.pth" % path_best_train)

            if epoch >= args.testing_set and best_test > test_loss_total:
                best_test = test_loss_total

                best_state.test.epoch = epoch + 1
                set_state(best_state.test.train, train_loss_total)
                set_state(best_state.test.test, test_loss_total)

                copy_file("%s.pth" % path_latest, "%s.pth" % path_best_test)

            save_json(path_model_info, self.current_state)

        model.compile(self.optimizer)

        if np.isfinite(args.epochs):
            for epoch in range(last_state.epoch, args.epochs):
                do_epoch(epoch)
        else:
            epoch = last_state.epoch

            while True:
                do_epoch(epoch)
                epoch = epoch + 1

        summary_training.close()
        summary_testing.close()

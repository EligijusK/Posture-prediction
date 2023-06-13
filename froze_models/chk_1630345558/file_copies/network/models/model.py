import torch as _torch
import torch.nn as _tnn
from .sit_straight import SitStraightNet as _SitStraightNet
from .full_model import FullModel as _FullModel
from network.scaled_optimizer import ScaledOptimizer as _ScaledOptimizer
from tqdm import tqdm as _tqdm


class Model:
    def __init__(self, *, in_points, use_preprocessed, label_count):
        self.ssnet = network = _SitStraightNet(
            in_points=in_points, use_preprocessed=use_preprocessed, label_count=label_count)

        network = _FullModel(network)
        network = _tnn.DataParallel(network).cuda()

        self.model = network
        self.optimizer: _ScaledOptimizer = None

    def compile(self, optimizer: _ScaledOptimizer):
        self.optimizer = optimizer
        optimizer.compile(self.ssnet.parameters())

    def fit(self, dataset, epochs=1):
        self.ssnet.train()

        history = []

        for i in range(epochs):
            self.ssnet.on_before_epoch()
            its, epoch_metrics = 0, {"loss": {"loss": 0}, "accuracy": {}}
            epoch_loss, epoch_acc = epoch_metrics["loss"], epoch_metrics["accuracy"]

            it_tqdm = _tqdm(dataset)
            for data in it_tqdm:
                step_metrics = self.train_step(data)
                loss_metrics, acc_metrics = step_metrics["loss"], step_metrics["accuracy"]

                for key in loss_metrics:
                    value = loss_metrics[key]

                    if key not in epoch_loss:
                        epoch_loss[key] = value
                    else:
                        epoch_loss[key] += value

                    epoch_loss["loss"] += value

                for key in acc_metrics:
                    value = acc_metrics[key]

                    if key not in epoch_acc:
                        epoch_acc[key] = value
                    else:
                        epoch_acc[key] += value

                its += 1

                it_tqdm.set_description("loss: %.8E | acc: %f" %
                                        (epoch_loss["loss"] / its, epoch_acc["acc"] / its))

            for key in epoch_loss:
                epoch_loss[key] /= its

            for key in epoch_acc:
                epoch_acc[key] /= its

            history.append(epoch_metrics)

            self.optimizer.step(epoch_loss["loss"])

        return {"history": history}

    def predict(self, t_in):
        ssnet = self.ssnet

        ssnet.eval()

        with _torch.no_grad():
            t_in = t_in.float().cuda().contiguous()
            t_out = self.ssnet(t_in)

            return _torch.sigmoid(t_out)

    def restore(self, path, load_optimizer):
        state = _torch.load(path)

        self.ssnet.load_state_dict(state["state_model"])

        if load_optimizer:
            self.optimizer.load_state_dict(state["state_optimizer"])

    def train_step(self, t_data):
        opt = self.optimizer

        with _torch.cuda.amp.autocast(enabled=opt.use_mixed_precision):
            t_data = [t.float().cuda().contiguous() for t in t_data[1:]]

            loss, accuracy = self.model(t_data)
            loss_net = loss.mean()
            acc_net = accuracy.mean()

        opt.backward(loss_net)

        return {
            "loss": {"bce": loss_net.item()},
            "accuracy": {"acc": acc_net.item()}
        }

    def evaluate(self, dataset):
        self.ssnet.eval()

        with _torch.no_grad():
            its, epoch_metrics = 0, {"loss": {"loss": 0}, "accuracy": {}}
            epoch_loss, epoch_acc = epoch_metrics["loss"], epoch_metrics["accuracy"]

            it_tqdm = _tqdm(dataset)
            for data in it_tqdm:
                step_metrics = self.eval_step(data)
                loss_metrics, acc_metrics = step_metrics["loss"], step_metrics["accuracy"]

                for key in loss_metrics:
                    value = loss_metrics[key]

                    if key not in epoch_loss:
                        epoch_loss[key] = value
                    else:
                        epoch_loss[key] += value

                    epoch_loss["loss"] += value
                
                for key in acc_metrics:
                    value = acc_metrics[key]

                    if key not in epoch_acc:
                        epoch_acc[key] = value
                    else:
                        epoch_acc[key] += value

                its += 1

                it_tqdm.set_description("eval loss: %.8E | acc: %f" %
                                        (epoch_loss["loss"] / its, epoch_acc["acc"] / its))

            for key in epoch_loss:
                epoch_loss[key] /= its

            for key in epoch_acc:
                epoch_acc[key] /= its

        return epoch_metrics

    def eval_step(self, t_data):
        opt = self.optimizer

        with _torch.cuda.amp.autocast(enabled=opt.use_mixed_precision):
            t_data = [t.float().cuda().contiguous() for t in t_data[1:]]

            loss, accuracy = self.model(t_data)
            loss_net = loss.mean()
            acc_net = accuracy.mean()

        return {
            "loss": {"bce": loss_net.item()},
            "accuracy": {"acc": acc_net.item()}
        }

    def save_weights(self, path):
        _torch.save({
            "state_model": self.ssnet.state_dict(),
            "state_optimizer": self.optimizer.state_dict()
        }, path)

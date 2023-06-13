import torch as _torch
import torch.optim as _optim


class ScaledOptimizer:
    def __init__(self, learning_rate, mixed_precision=True):
        super(ScaledOptimizer, self).__init__()

        self.initial_lr = learning_rate
        self.weight_decay = 1e-5
        self.use_mixed_precision = mixed_precision
        self.optimizer: _optim.Adam = None
        self.scheduler: _optim.lr_scheduler.LambdaLR = None
        self.enabled = True

    def compile(self, parameters):
        self.optimizer = _optim.Adam(
            parameters,
            lr=self.initial_lr
        )
        self.scaler = _torch.cuda.amp.GradScaler(
            enabled=self.use_mixed_precision)

        self.scheduler = _optim.lr_scheduler.ReduceLROnPlateau(self.optimizer)

    def backward(self, loss):
        optimizer, scaler = self.optimizer, self.scaler

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        optimizer.zero_grad()

    def get_state(self): return self.optimizer.state_dict()
    def set_state(self, state): self.optimizer.load_state_dict(state)

    def step(self, train_loss): 
        self.scheduler.step(train_loss)

    @property
    def learning_rate(self):
        return self.optimizer.param_groups[0]["lr"]

    def state_dict(self):
        return self.optimizer.state_dict()

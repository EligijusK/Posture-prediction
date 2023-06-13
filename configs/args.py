import argparse
import configs.config as cfg
from math import isfinite, inf
from utils.sys_colors import BLUE, RESET
from configs.argtypes import strWithNone, str2bool, str2int_inf


__argparser = argparse.ArgumentParser(prog="Posture Network V2")
__argparser.add_argument("--epochs", type=str2int_inf,
                         required=False, default=cfg.TRAINING.EPOCHS)
__argparser.add_argument("--reduced_dataset", type=str2int_inf,
                         required=False, default=inf)
__argparser.add_argument("--load_optimizer", type=str2bool,
                         required=False, default=True)
__argparser.add_argument("--checkpoint", type=strWithNone,
                         required=False, default=None)
__argparser.add_argument("--checkpoint_type", type=str,
                         required=False, default="model")
__argparser.add_argument("--learning_rate", type=float,
                         required=False, default=cfg.TRAINING.LEARNING_RATE_INITIAL)
__argparser.add_argument("--batch_size", type=int,
                         required=False, default=cfg.TRAINING.BATCH_SIZE)
__argparser.add_argument("--testing_set", type=str2int_inf,
                         required=False, default=0)
__argparser.add_argument("--workers", type=int,
                         required=False, default=0)
__argparser.add_argument("--mixed_precision", type=str2bool,
                         required=False, default=True)
args = __argparser.parse_args()

print(BLUE + "---------------------------------------")
print("Launch Arguments:")
for arg in vars(args):
    value = str(getattr(args, arg))
    print("\t{:<20} {:>10}".format(arg, value))
print("---------------------------------------" + RESET)

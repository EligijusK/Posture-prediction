import numpy as np
import configs.config as cfg
from configs.args import args
from data.dataset import Dataset
from data.label_manager import LabelManager
from tqdm import tqdm
from utils.ply import export_ply
from network.network import Network

man_labels = LabelManager(cfg.DATA.PATH_TAXONOMY)

dataset = Dataset(
    dir_input=cfg.DATA.INPUTS,
    training_ratio=cfg.TRAINING.TRAINGING_SET_RATIO,
    augment=cfg.TRAINING.AUGMENT,
    depth_max=cfg.DATA.DEPTH.MAX,
    man_labels=man_labels
)

network = Network(man_labels=man_labels, checkpoint=args.checkpoint,
                  checkpoint_type=args.checkpoint_type)
network.train(dataset=dataset)
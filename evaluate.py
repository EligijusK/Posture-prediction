import cv2
import utils
import numpy as np
from tqdm import tqdm
# from network import StrippedNetwork as Network
from utils.network_bootstrap import get_network_constructor
from configs import config as cfg
from configs.args import args
from data.dataset import Dataset
from data.get_dataset import get_dataset
from data.label_manager import LabelManager
from data.recordings import Recordings
from network.models.full_model import FullModel

from sklearn.datasets import make_blobs
from sklearn.model_selection import LeaveOneOut
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier


def evaluate(r_fold, fold, checkpoint, checkpoint_type, data):
    recordings = Recordings(cfg.DATA.PATH_PEOPLE)
    man_labels = LabelManager(cfg.DATA.PATH_TAXONOMY)

    _, label_count, label_cache, _ = man_labels.label_cache
    root_elements = len(label_cache.children)
    root_names = [lab.name for lab in label_cache.children]
    dataset = Dataset(
        dataset=data,
        augment=cfg.TRAINING.AUGMENT,
        depth_max=cfg.DATA.DEPTH.MAX,
        man_labels=man_labels
    )

    def collect_labels(leaf, labels):
        if "children" in leaf:
            for i, ch in enumerate(leaf.children):
                labels[i + leaf.offset] = ch.name
                collect_labels(ch, labels)
        return labels

    all_labels = collect_labels(label_cache, [None] * (label_count + 11))
    all_labels[8:] = "expected_root", "expected_label", "pred_root", "pred_label", "root_ambiguity", "leaf_ambiguity", "person", "gender", "angle", "path"

    _, gen_testing = dataset.gen_batches(
        1,
        num_workers=args.workers
    )

    it_test = iter(gen_testing)

    dir_chekpoint = "%s/chk_%s" % (cfg.TRAINING.OUTPUT_MODELS, checkpoint)
    Network = get_network_constructor(checkpoint, True)
    network = Network(man_labels=man_labels,
                      path_weights="%s/%s.pth" % (dir_chekpoint, checkpoint_type))

    label_count = len(man_labels.available_labels)
    confusion_matrix = np.zeros([label_count, label_count], dtype=np.int)
    confusion_matrix_root = np.zeros(
        [root_elements, root_elements], dtype=np.int)

    ambiguity = [all_labels]

    indices = {}

    for i, label in enumerate(man_labels.available_labels):
        indices[label] = i

    for frame_data, inputs, outputs in tqdm(it_test, desc="prediction"):
        pred = network.predict(inputs)
        expt = outputs.cuda()

        slice_p = pred[..., :root_elements]
        slice_t = expt[..., :root_elements]

        racc = FullModel.accuracy(slice_p, slice_t).cpu().numpy()
        accu = FullModel.accuracy(pred, expt).cpu().numpy()

        pred = pred.detach().cpu().numpy()
        expt = expt.cpu().numpy()

        slice_p = slice_p.cpu().numpy()
        slice_t = slice_t.cpu().numpy()

        fold.append(float(accu))
        r_fold.append(float(racc))

        root_p = np.argmax(slice_p, axis=-1)
        root_t = np.argmax(slice_t, axis=-1)

        sorted_p = np.argsort(slice_p, axis=-1)[..., ::-1]

        pred_labels = [man_labels.get_label(val) for val in pred]
        pred_ambiguity = [man_labels.get_ambiguity(val) for val in pred]
        true_labels = [man_labels.get_label(val) for val in expt]

        for i, pred_label in enumerate(pred_labels):
            person = recordings.get_person(frame_data["name"][i])
            image = inputs[i, 0]
            true_label, true_label_root = true_labels[i], root_names[root_t[i]]
            pred_label_root = root_names[root_p[i]]

            root_ambiguity = float(
                slice_p[i, sorted_p[i][1]] / slice_p[i, sorted_p[i][0]])

            index_p, index_t = indices[pred_label[0]], indices[true_label[0]]
            "person", "gender", "angle", "path"
            combined = np.concatenate([
                pred[i],
                np.array([true_label_root, true_label]),
                np.array([pred_label_root, pred_label]),
                np.array([root_ambiguity, pred_ambiguity[i]]),
                np.array([person.person_id, person.gender,
                          person.angle, frame_data["path"][0]])
            ], axis=-1)
            ambiguity.append(combined)

            confusion_matrix[index_p, index_t] += 1
            confusion_matrix_root[root_p[i], root_t[i]] += 1

    with open("%s/ambiguities_%s.csv" % (dir_chekpoint, checkpoint_type), "w") as f:
        for line in tqdm(ambiguity, desc="Ambiguity"):
            f.write(",".join([str(x)
                              for x in line]))
            f.write('\n')

        # f.write(",".join(man_labels.available_labels))
        # f.write("\n")
        # f.write(",".join([str(x) for x in ambiguity[..., 0] / ambiguity[..., 1]]))

    with open("%s/confussion_%s.csv" % (dir_chekpoint, checkpoint_type), "w") as f:
        f.write(",")
        f.write(",".join(man_labels.available_labels))

        for i, label in enumerate(tqdm(man_labels.available_labels, desc="confussion_all")):
            f.write("\n")
            f.write(label)
            f.write(",")
            f.write(",".join([str(x) for x in confusion_matrix[i]]))

    with open("%s/root_confussion_%s.csv" % (dir_chekpoint, checkpoint_type), "w") as f:
        f.write(",")
        f.write(",".join(root_names))

        for i, label in enumerate(tqdm(root_names, desc="confussion_root")):
            f.write("\n")
            f.write(label)
            f.write(",")
            f.write(",".join([str(x) for x in confusion_matrix_root[i]]))


# checkpoint = "1617045266"
checkpoint_type = "model_best_test"

checkpoint_list = ["1617096225",
                   "1617102559",
                   "1617108877",
                   "1617115199",
                   "1617121557",
                   "1617127890",
                   "1617134237",
                   "1617140578",
                   "1617146940",
                   "1617153267",
                   "1617159631"]

r_folds, folds = [], []
data_list = get_dataset(cfg.DATA.PATH_PEOPLE, cfg.DATA.INPUTS)

for fold_index, (checkpoint, data) in enumerate(zip(checkpoint_list, data_list)):
    fold_name = "fold_%i" % (fold_index + 1)
    r_fold, fold = [fold_name], [fold_name]
    r_folds.append(r_fold)
    folds.append(fold)

    evaluate(r_fold, fold, checkpoint, checkpoint_type, data)

with open("outputs/r_folds.csv", "w") as f:
    for data in zip(*r_folds):
        f.write(",".join([str(f) for f in data]))
        f.write("\n")

with open("outputs/folds.csv", "w") as f:
    for data in zip(*folds):
        f.write(",".join([str(f) for f in data]))
        f.write("\n")
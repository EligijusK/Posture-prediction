import numpy as np
import json
from easydict import EasyDict
from scipy.special import softmax


class HierarchicalClass:
    def __init__(self, data, *, level=0, parent=None):
        self.level = level
        self.name = data["name"]
        self.colorText = data["colorText"][::-
                                           1] if "colorText" in data else None
        self.colorRect = data["colorRect"][::-
                                           1] if "colorRect" in data else None
        self.children = [HierarchicalClass(
            x, level=level + 1, parent=self) for x in (data["children"] if data.get("children") else [])]
        self.color = np.random.rand(3,)
        self.parent = parent

    def get_hierarchy_map(self, *, out_result={}, out_leaves={}):
        if out_result.get(self.name):
            raise Exception("Collision detected")
        out_result[self.name] = self

        if len(self.children) != 0:
            [x.get_hierarchy_map(out_result=out_result,
                                 out_leaves=out_leaves) for x in self.children]
        else:
            out_leaves[self.name] = self

        return out_result, out_leaves

    def get_shape(self, parent=None):
        shape = len(self.children)

        if shape <= 1:
            return EasyDict({
                "colorText": self.colorText,
                "colorRect": self.colorRect,
                "leaf_node": True
            })

        children = {}
        children_indices = []

        for ch in self.children:
            children[ch.name] = ch.get_shape(self)
            children_indices.append(ch.name)

        return EasyDict({
            "name": self.name,
            "colorText": self.colorText,
            "colorRect": self.colorRect,
            "shape": shape,
            "children": children,
            "children_indices": children_indices,
            "parent": parent.name if parent else None,
            "leaf_node": False
        })


class LabelManager:
    def __init__(self, path_label_hierarchy, allow_unknown=True):
        with open(path_label_hierarchy) as f:
            self.__hierarchy = HierarchicalClass(json.load(f))

        self.__map_hierarchy, self.__map_leaves = self.__hierarchy.get_hierarchy_map()
        self.__keys_hierarchy = self.__map_hierarchy.keys()
        self.__keys_leaves = self.__map_leaves.keys()

        self.__allow_unknown = allow_unknown
        self.__labels = []
        self.__is_labeling = False
        self.__label_time_begun = 0

        self.__label_cache = self.__create_array_cache()

    @property
    def label_cache(self):
        return self.__label_cache

    def get_label(self, array):
        _, _, label_map, _ = self.__label_cache

        if self.__allow_unknown and np.max(array) < 0.2:
            return "unknown", [0, 0, 0], [255, 255, 255]

        def get_label(value, leaf):

            if "children" not in leaf:
                return leaf.name, leaf.colorText, leaf.colorRect

            offset_start = leaf.offset
            offset_end = len(leaf.children) + offset_start

            array = value[offset_start:offset_end]
            arg_max = np.argmax(array)

            return get_label(value, leaf.children[arg_max])

        return get_label(array, label_map)

    def get_ambiguity(self, array):
        _, _, label_map, _ = self.__label_cache

        def get_ambiguity(value, leaf):

            offset_start = leaf.offset
            offset_end = len(leaf.children) + offset_start

            array = value[offset_start:offset_end]
            arg_max = np.argmax(array)

            if "children" not in leaf.children[arg_max]:
                # arg_soft = softmax(array)
                arg_soft = array
                sorted_p = np.argsort(arg_soft, axis=-1)[..., ::-1]
                ambiguity = arg_soft[sorted_p[1]] / arg_soft[sorted_p[0]]

                return ambiguity

            return get_ambiguity(value, leaf.children[arg_max])

        return get_ambiguity(array, label_map)

    def __create_array_cache(self):
        out_shape = self.get_shape()
        available_labels = self.available_labels
        out_labels = []
        label_mapper = EasyDict({
            "index": -1,
            "offset": 0,
            "colorText": None,
            "colorRect": None
        })
        label_count = len(available_labels)

        offset = 0

        def construct_tree(node, map_data):
            nonlocal offset
            map_data.name = node.name
            _len = 0

            if node.children is not None:
                ch_count = len(node.children)
                map_data.children = [None] * ch_count
                map_data.children_map = {}

                _len += ch_count
                offset += ch_count

                for i, key in enumerate(node.children):
                    ch = node.children[key]
                    leaf = EasyDict({
                        "name": key,
                        "index": i,
                        "offset": offset,
                        "parent": map_data,
                        "colorText": ch.colorText,
                        "colorRect": ch.colorRect
                    })
                    map_data.children_map[key] = leaf
                    if ch.leaf_node is not True:
                        _len += construct_tree(ch, leaf)
                    map_data.children[i] = leaf

            return _len

        array_length = construct_tree(out_shape, label_mapper)

        cached_classifier, cached_colors = {}, {
            "unknown": EasyDict({
                "colorText": [0, 0, 0],
                "colorRect": [255, 255, 255]
            }),
            "empty": EasyDict({
                "colorText": [255, 255, 255],
                "colorRect": [0, 0, 0]
            })
        }

        for i, label in enumerate(available_labels):
            cached_classifier[label] = arr = np.zeros(
                array_length, dtype=np.float32)

            mapper = label_mapper

            for link in self.get_label_chain(label):
                mapper = mapper.children_map[link]
                parent = mapper.parent

                arr[parent.offset + mapper.index] = 1

                cached_colors[mapper.name] = EasyDict({
                    "colorText": mapper.colorText,
                    "colorRect": mapper.colorRect
                })

        return cached_classifier, array_length, label_mapper, cached_colors

    @property
    def is_labeling(self):
        return self.__is_labeling

    def get_shape(self):
        return self.__hierarchy.get_shape()

    @property
    def begin_time(self):
        return self.__label_time_begun

    def get_color(self, label):
        element = self.__map_hierarchy.get(label)

        if not element:
            return np.random.rand(3,)

        return element.color

    def get_label_chain(self, name):
        chain = []

        def get_chain(name):
            hierarchy = self.__map_hierarchy.get(name)

            parent = hierarchy.parent

            if parent:
                chain.insert(0, name)
                get_chain(parent.name)

        get_chain(name)

        return chain

    def get_accuracy(self, predicted_name, actual_name):
        chain_predicted = self.get_label_chain(predicted_name)
        chain_actual = self.get_label_chain(actual_name)

        len_predicted = len(chain_predicted)
        len_actual = len(chain_actual)
        len_max = max(len_predicted, len_actual)

        accuracy = []
        multipliers = softmax(np.array([np.exp(i) for i in range(len_max)]))

        for i in range(len_max):
            predicted = chain_predicted[i] if i < len_predicted else None
            actual = chain_actual[i] if i < len_actual else None

            cur_accuracy = (1 if predicted == actual else 0) * multipliers[i]

            accuracy.append(cur_accuracy)

        return np.round(np.sum(accuracy), decimals=5)

    @property
    def available_labels(self):
        return [x for x in self.__keys_leaves]

    def get_current_label(self, time):
        best_label = None

        for label in self.__labels:
            if label.min <= time and time <= label.max:
                best_label = label.label

        return best_label

    def set_start_time(self, time):
        self.__is_labeling = True
        self.__label_time_begun = time

    def set_finish_time(self, time, label):
        if not self.__is_labeling:
            return

        time_min = np.min([self.__label_time_begun, time])
        time_max = np.max([self.__label_time_begun, time])

        self.__labels.append(EasyDict({
            "label": label,
            "min": time_min,
            "max": time_max
        }))

        self.__is_labeling = False

    def get_timeline(self):
        timeline = self.__labels
        has_merged = True

        while has_merged:
            timeline, has_merged = get_timeline(timeline)

        return timeline

    def save(self, path):
        timeline = self.get_timeline()

        with open(path, "w") as f:
            json.dump(timeline, f)


def get_timeline(unmerged_labels):
    buckets = []

    def ranges_intersect(x, y):
        return max(x.min, y.min) < min(x.max, y.max)

    def splice_ranges(x, y):
        if x.label == y.label:
            return [EasyDict({
                "label": x.label,
                "min": np.min([x.min, y.min]),
                "max": np.max([x.max, y.max])
            })]

        dt_min = x.min - y.min
        dt_max = y.max - x.max

        is_fully_encompassed = dt_min <= 0 and dt_max <= 0

        if is_fully_encompassed:
            return [x]

        splices = []

        if dt_min > 0:
            splice = EasyDict({
                "label": y.label,
                "min": y.min,
                "max": x.min
            })

            splices.append(splice)

        splices.append(x)

        if dt_max > 0:
            splice = EasyDict({
                "label": y.label,
                "min": x.max,
                "max": y.max
            })

            splices.append(splice)

        return splices

    def find_intersections(label, buckets):
        intersecting_indices = []

        for i in range(len(buckets)):
            other_label = buckets[i]

            if ranges_intersect(label, other_label):
                intersecting_indices.append(i)

        return intersecting_indices

    has_merged = False

    for i in range(len(unmerged_labels)):
        label = unmerged_labels[i]
        checking_index = 0

        intersecting_indices = find_intersections(label, buckets)

        if len(intersecting_indices) == 0:
            buckets.append(label)
        else:
            for intersecting_index in intersecting_indices:
                other_label = buckets.pop(intersecting_index)

                spliced = splice_ranges(label, other_label)

                [buckets.append(x) for x in spliced]

                has_merged = True

    return buckets, has_merged

import os
from time import time as now
import configs.config as cfg
from data.label_manager import LabelManager

class AppLabels:
    def __init__(self, dirname):
        self.man_labels, self.label_cache, self.color_cache = \
            self.__get_label_manager(dirname)

        self.last_label_time = now()

    def __get_label_manager(self, dirname):
        path_taxonomy = "%s/%s" % (dirname, cfg.DATA.PATH_TAXONOMY)
        man_labels = LabelManager(os.path.realpath(path_taxonomy))

        label_cache, _, _, color_cache = man_labels.label_cache

        return man_labels, label_cache, color_cache

    def __update_labels(self, new_label):
        if (self.last_prediction[0] != "take break" or new_label[0] == "away") and self.last_prediction[0] != new_label[0]:
            last_label_time = now()
            
            self.last_prediction = new_label
            
            self._AppAudio__from_label(last_label_time)
            self._AppNotifications__from_label(last_label_time)

        self._AppAudio__update_sound()
        self._AppNotifications__update_notifications()

        # if self.last_prediction[0] != "take break":
        #     self.last_prediction = new_label


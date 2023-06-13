import os
from configparser import ConfigParser
from app.configs.models import Models
# from app.configs.sounds import Sounds
# from app.configs.notifications import Notifications
from app.configs.history import History

from app.configs.bad_posture import BadPosture
from app.configs.take_break import TakeBreak


class AppConfigs:
    def __init__(self, path_configs):
        configs = ConfigParser()

        if os.path.exists(path_configs):
            configs.read(path_configs)

        self.__configs = configs

        self.__section_take_break = TakeBreak(configs)
        self.__section_bad_posture = BadPosture(configs)

        self.__section_models = Models(configs)
        # self.__section_sounds = Sounds(configs)
        self.__section_history = History(configs)
        # self.__section_notifications = Notifications(configs)
        self.__path_configs = path_configs

    @property
    def TAKE_BREAK(self): return self.__section_take_break

    @property
    def BAD_POSTURE(self): return self.__section_bad_posture

    @property
    def MODEL(self): return self.__section_models

    # @property
    # def SOUND(self): return self.__section_sounds

    @property
    def HISTORY(self): return self.__section_history

    # @property
    # def NOTIFICATIONS(self): return self.__section_notifications

    def save(self):
        with open(self.__path_configs, "w") as file:
            self.__configs.write(file, True)

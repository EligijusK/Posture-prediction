from time import time as now
from easydict import EasyDict


class AppAudio:
    def __init__(self, *args, **kwargs):
        self.notes = self.__load_sounds()
        self.last_sound_time, self.note = now(), None

    def __get_label_sound_info(self):
        label, _, _, _ = self.last_prediction

        if label == "take break":
            return self.notes.low_pitch
        elif label == "bad":
            return self.notes.high_pitch

        return None

    def __load_sounds(self):
        import pygame
        from app.note import Note

        pygame.mixer.pre_init(44100, -16, 1, 1024)
        pygame.init()

        return EasyDict({
            "low_pitch": Note(100),
            "high_pitch": Note(500)
        })

    def __from_label(self, last_label_time):
        self.note = self.__get_label_sound_info()

        self.last_sound_time = \
            self.last_sound_time = self.last_prediction[1] - self.config.TAKE_BREAK.NOTIFICATION_TIME * 60 \
            if self.last_prediction[0] == "take break" \
            else last_label_time

    def __update_sound(self):
        current_timestamp = now()

        # print(current_timestamp - self.last_sound_time)
        if self.note:
            section = self.config.TAKE_BREAK \
                if self.last_prediction[0] == "take break" \
                else self.config.BAD_POSTURE

            if section.NOTIFICATION_SOUND:
                if current_timestamp >= self.last_sound_time + section.NOTIFICATION_TIME * 60:
                    self.note.play(50)

                    self.last_sound_time = current_timestamp

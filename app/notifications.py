from time import time as now
from easydict import EasyDict

APP_NAME = "SitYEA"


class AppNotifications:
    def __init__(self, dirname, *args, **kwargs):
        self.notifications = self.__load_notifications(dirname)
        self.last_notify_time, self.message = now(), None

    def __load_notifications(self, dirname):
        from platform import system

        app_icon = "%s/images/ico.ico" % dirname

        if system() == "Windows":
            from app.win_notify import Notify
        else:
            from notifypy import Notify

        return EasyDict({
            "fuck_off": Notify("Take a break", "You've been sitting too long, consider taking a break.", APP_NAME, app_icon),
            "hunching": Notify("Sit straight", "You're hunched for a while - try sitting straight!", APP_NAME, app_icon),
            "lying_down": Notify("Sit straight", "You're lying in the chair for a while - try sitting straight!", APP_NAME, app_icon),
            "exception": Notify("Error encountered", "An exception has been encountered.", APP_NAME, app_icon),
            "exception_rs": Notify("Error encountered", "A problem with Realsense encountered, attempting to reset the device. If this continues to happen, plug the device back in.", APP_NAME, app_icon),
            "calibration": Notify("Check calibration", "Calibration seems to be off.", APP_NAME, app_icon),
        })

    def __get_label_notify_info(self):
        _, _, label, _ = self.last_prediction

        if label == "take break":
            return self.notifications.fuck_off
        elif label == "lightly hunching" or label == "hunching" or label == "extremely hunched":
            return self.notifications.hunching
        elif label == "partially lying" or label == "lying down":
            return self.notifications.lying_down

        return None

    def __from_label(self, last_label_time):
        self.message = self.__get_label_notify_info()
        self.last_notify_time = \
            self.last_notify_time = self.last_prediction[1] - self.config.TAKE_BREAK.NOTIFICATION_TIME * 60 \
            if self.last_prediction[0] == "take break" \
            else last_label_time

    def __update_notifications(self):
        current_timestamp = now()

        # print(current_timestamp - self.last_notify_time)
        if self.message:
            section = self.config.TAKE_BREAK \
                if self.last_prediction[0] == "take break" \
                else self.config.BAD_POSTURE

            if section.NOTIFICATION_DESKTOP:
                if current_timestamp >= self.last_notify_time + section.NOTIFICATION_TIME * 60:
                    self.message.send()

                    self.last_notify_time = current_timestamp


if __name__ == "__main__":
    pass

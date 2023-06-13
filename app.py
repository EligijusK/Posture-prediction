import os
import numpy as np
from configparser import ConfigParser
import tkinter as tk
import threading
import time
import tkinter.font
from PIL import Image as pilImage, ImageTk as pilImageTk
import pyrealsense2 as rs
import configs.config as config
from app.config import AppConfigs
from app.realsense import AppRealsense
from app.audio import AppAudio
from app.notifications import AppNotifications
from app.images import AppImages
from app.labels import AppLabels
from app.model import AppModel
from app.frame import AppFrame
from app.user_interface import AppUI, UI_TYPES
from app.wanker_protect import AppWankerProtect
from time import time as now
from utils.get_asset import get_asset_path
from cefpython3 import cefpython as cef

PATH_CONFIG = "settings.ini"

HEIGHT, WIDTH, _ = config.DATA.RESOLUTION.FRAME


class App(tk.Frame, AppRealsense, AppAudio, AppNotifications, AppImages, AppLabels, AppModel, AppFrame, AppUI):
    def __init__(self, *, master=None, load_model, enable_rs, override_device=None):
        self.config = AppConfigs(PATH_CONFIG)
        self.is_running = False
        self.start_time = now()

        dirname = get_asset_path()

        tk.Frame.__init__(self, master)
        AppRealsense.__init__(self, enable_rs, override_device)
        AppAudio.__init__(self)
        AppNotifications.__init__(self, dirname)
        AppImages.__init__(self, dirname)
        AppLabels.__init__(self, dirname)
        AppModel.__init__(self, self.shared_buffer, enable_rs and load_model,
                          self.config.MODEL.PATH_MODEL,
                          self.config.MODEL.PATH_CHECKPOINT)
        AppFrame.__init__(self)
        AppUI.__init__(self)

    @property
    def frame_aspect_ratio(self): return WIDTH / HEIGHT
    @property
    def frame_height(self): return 258
    @property
    def frame_width(self):
        return round(self.frame_aspect_ratio * self.frame_height)

    @property
    def frame_offset_height(self): return 273
    @property
    def frame_offset_width(self): return 115

    def __save_exception(self):
        import sys
        import datetime
        import traceback

        with open("error.log", "a") as f:
            stacktrace = "".join(traceback.format_exception(*sys.exc_info()))

            f.write("[%s]\n" % str(datetime.datetime.now()))
            f.write(stacktrace)
            f.write("\n\n")

            print(stacktrace)

    def start(self):
        height, width, _ = np.shape(self.img_background)

        self.master.minsize(width, height)
        self.pack(fill="both", expand=True)
        self.is_running = True

        has_rs = self.pipeline is not None
        has_tf = self.has_tf

        canvas = self.canvas
        canvas.config(width=width, height=height)
        canvas.place(x=0, y=0)

        settings_image: pilImage.Image = pilImageTk.PhotoImage(
            image=self.img_settings)
        silhouette = self._AppFrame__get_framed(
            self.img_silhouette, (width, height), True)
        font = tk.font.Font(size=24)
        image = pilImageTk.PhotoImage(pilImage.new("RGBA", (width, height)))

        try:
            thread_locked = False

            def on_thread():
                nonlocal thread_locked
                while self.is_running:
                    composite: pilImage.Image = None

                    if self.ui_open == UI_TYPES.CALIBRATE:
                        composite = self.img_calibration
                    elif self.ui_open == UI_TYPES.EXERCISES:
                        composite = self.img_exercises
                    elif self.ui_open == UI_TYPES.WORKSPACE:
                        composite = self.img_workspace
                    else:
                        composite = self.img_background

                    needs_prediction = True

                    if has_rs:
                        try:
                            self._AppRealsense__get_frame_data()
                        except:
                            self._AppRealsense__reset_realsense()
                            self.notifications.exception_rs.send()
                            self.__save_exception()
                            continue

                        self.predict_face()

                    if self.ui_open == UI_TYPES.CALIBRATE:
                        pred_label, color_text, color_rect = \
                            self._AppModel__get_prediction() if has_tf and has_rs \
                            else ("RS DISABLED", [255, 255, 255], [0, 0, 0])

                        
                        self._AppLabels__update_labels(
                            self.label_to_prediction(pred_label))

                        display_frame = self._AppRealsense__get_rs_frame(
                            (width, height))

                        composite = pilImage.composite(
                            display_frame, composite, display_frame)

                        image.paste(composite)

                        canvas.create_image(0, 0, image=image, anchor=tk.NW)

                        self._AppUI__draw_prediction(
                            canvas, font, pred_label, color_text, color_rect)
                    elif self.ui_open == UI_TYPES.EXERCISES or self.ui_open == UI_TYPES.WORKSPACE:
                        image.paste(composite)
                        canvas.create_image(
                            0, 0, image=image, anchor=tk.NW)

                        needs_prediction = False
                    else:
                        if self.has_tf and self._AppModel__is_ready():
                            pred_label, color_text, color_rect = \
                                self._AppModel__get_prediction() if has_tf and has_rs \
                                else ("RS DISABLED", [255, 255, 255], [0, 0, 0])

                            self.add_prediction(pred_label)

                            if self.config.MODEL.CALIBRATION_ENABLED:
                                self.check_calibration()

                            self._AppLabels__update_labels(
                                self.label_to_prediction(pred_label))

                        charts = self.cur_figs

                        composite = pilImage.composite(
                            charts, composite, charts)

                        composite = self.draw_clickable_buttons(composite)

                        image.paste(composite)
                        canvas.create_image(
                            0, 0, image=image, anchor=tk.NW)

                    if needs_prediction:
                        if now() > self.start_time + self.config.TAKE_BREAK.NOTIFICATION_TIME * 60:
                            self._AppUI__draw_fuck_off(canvas, font)
                            self._AppLabels__update_labels(
                                self.label_to_prediction("take break"))

                        if self.has_tf:
                            self._AppModel__try_poll()

                    time.sleep(0.19)
                self.quit()

            thread = threading.Thread(target=on_thread)

            def main_loop():
                nonlocal thread_locked
                if self.ui_open == UI_TYPES.DASHBOARD:
                    thread_locked = True
                    self._AppUI__draw_current()
                    self._AppUI__draw_total()
                    self._AppUI__get_history_figure(
                        (width, height))
                    thread_locked = False
                if self.is_running:
                    self.after(self.config.HISTORY.TIME_PREDICTION, main_loop)

            main_loop()
            thread.start()
            app.mainloop()
        except Exception as e:
            self.__save_exception()
            self.notifications.exception.send()

        if has_tf:
            self.pipeline.stop()

        self.destroy()

    def label_to_prediction(self, label):
        if label == "sitting straight":
            new_label = "good"
        elif label == "unknown" or label == "take break" or label == "away":
            new_label = label
        else:
            new_label = "bad"

        old_label, old_timestamp, _, _ = self.last_prediction
        timestamp = now()

        if old_label == new_label:
            return (old_label, old_timestamp, label, timestamp)

        return (new_label, now(), label, timestamp)


if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()

    anti_wank = AppWankerProtect()

    if anti_wank.start():
        context = rs.context()
        devices = context.query_devices()

        override_device = "/home/ratchet/Downloads/RS_D435I_20210428_175414.bag"

        if "override_device" not in globals():
            override_device = None

        app = App(
            load_model=True,
            enable_rs=len(devices) > 0 or override_device is not None,
            override_device=override_device
        )
        cef.Initialize()
        app.start()
        cef.Shutdown()
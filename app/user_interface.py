import os
import sys
import cv2
import numpy as np
import tkinter.font
import tkinter as tk
import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image as pilImage
from app.browser_frame import BrowserFrame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

mpl.use("TkAgg")
PATH_HISTORY = "history.npy"


class UI_TYPES:
    DASHBOARD = "dashboard"
    CALIBRATE = "calibrate"
    WORKSPACE = "workspace"
    EXERCISES = "exercises"


class AppUI:
    def __init__(self):
        self.bind_all("<KeyPress>", self.on_key_press)
        self.master.protocol("WM_DELETE_WINDOW", self.on_window_close)

        self.history_all = np.load(PATH_HISTORY) if os.path.exists(
            PATH_HISTORY) else np.zeros(4)

        self.master.title("SitYEA")
        self.master.resizable(False, False)

        self.is_settings_open = False
        self.ui_open = UI_TYPES.DASHBOARD
        self.ui_prev = None

        self.history_current = np.zeros(
            [self.config.HISTORY.HISTORY_BUCKET_COUNT, 4], dtype=np.uint8)

        self.figures, self.canvas = self.__create_elements()

        self.buttons = self.__create_buttons()

        height, width, _ = np.shape(self.img_background)

        self.click_frame = pilImage.new("RGBA", (width, height))

        if not getattr(sys, "frozen", False):
            self.dbg_buffer = np.zeros([height, width, 4], dtype=np.uint8)
            self.dbg_image = pilImage.fromarray(self.dbg_buffer)

        self.act_figs = pilImage.new("RGBA", (width, height))
        self.cur_figs = pilImage.new("RGBA", (width, height))
        # self.rendered_figs = False

    def __draw_fuck_off(self, canvas, font: tk.font.Font):
        message = "Take a break"
        size = font.measure(message)
        metrics = font.metrics()
        ascent = metrics["ascent"]

        box_x, box_y = 200, 800

        canvas.create_rectangle(
            box_x, box_y - ascent, box_x + size, box_y + ascent, fill="#%02x%02x%02x" % tuple((0, 0, 0)))

        canvas.create_text(box_x, box_y, font=font, anchor="w",
                           text=message, fill="#%02x%02x%02x" % tuple((255, 0, 0)))

    def __draw_prediction(self, canvas, font: tk.font.Font, pred_label, color_text, color_rect):
        size = font.measure(pred_label)
        metrics = font.metrics()
        ascent = metrics["ascent"]

        box_x, box_y = 735, 560

        canvas.create_rectangle(
            box_x, box_y - ascent, box_x + size, box_y + ascent, fill="#%02x%02x%02x" % tuple(color_rect))

        canvas.create_text(box_x, box_y, font=font, anchor="w",
                           text=pred_label, fill="#%02x%02x%02x" % tuple(color_text))

    def add_prediction(self, pred):
        index = \
            0 if pred == "empty" else \
            1 if pred == "unknown" else \
            2 if pred == "sitting straight" else \
            3

        if self.history_current[-1].sum() >= self.config.HISTORY.HISTORY_BUCKET_SIZE:
            self.history_current[0:-1] = self.history_current[1:]
            self.history_current[-1] = 0

        self.history_all[index] += 1
        self.history_current[-1][index] += 1

        self.save_history()

    def __draw_current(self):
        fig, _ = self.figures
        emp, unk, good, bad = self.history_current.T

        time = [*range(len(self.history_current))]

        plt.figure(fig.number)
        plt.clf()
        plt.bar(time, good, color="#2ED47A", width=0.55)
        plt.bar(time, bad, bottom=good, color="#F7685B", width=0.55)
        # plt.bar(time, unk, bottom=good + bad, color="C1", width=0.55)
        plt.bar(time, emp, bottom=good + bad, color="#FFB946", width=0.55)
        plt.ylim(0, self.config.HISTORY.HISTORY_BUCKET_SIZE)
        plt.axis("off")

        # redraw the canvas
        fig.canvas.draw()

    def save_history(self):
        np.save(PATH_HISTORY, self.history_all)

    def __draw_total(self):
        _, fig = self.figures
        away, _, good, bad = self.history_all.T

        sizes = [away, good, bad]
        # labels = "Away", "Correct", "Incorrect"

        plt.figure(fig.number)
        plt.clf()

        if good == 0 and bad == 0:
            plt.pie([1], shadow=True, startangle=90, colors=["#2ED47A"])
        else:
            plt.pie(sizes, explode=(0, 0, 0.1),
                    shadow=True, startangle=90, colors=["#FFB946", "#2ED47A", "#F7685B"])

        plt.axis("equal")

        # redraw the canvas
        fig.canvas.draw()

    def flip_figures(self):
        self.act_figs, self.cur_figs = self.cur_figs, self.act_figs
        # self.rendered_figs = False

    def __get_history_figure(self, frame_size):
        self.flip_figures()
        act_figs = self.act_figs

        # if self.rendered_figs:
        #     return act_figs

        def get_numpy(xy, fig):
            if not hasattr(fig.canvas, "renderer"):
                return None

            # convert canvas to image
            frame = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8,
                                  sep='')
            frame = frame.reshape(
                fig.canvas.get_width_height()[::-1] + (3,))

            act_figs.paste(pilImage.fromarray(frame), xy)

            return act_figs

        [
            get_numpy(xy, fig)
            for xy, fig in zip(
                [(250, 125), (850, 470)],
                self.figures
            )
        ]

        # self.rendered_figs = True

        # return act_figs

    def show_ui(self, ui_type):
        if self.ui_open == ui_type:
            return
            # if self.ui_prev == None:
            #     return

            # ui_type = self.ui_prev

        if ui_type == UI_TYPES.DASHBOARD:
            self.set_fields_visible(True)
        else:
            self.set_fields_visible(False)

        if ui_type == UI_TYPES.WORKSPACE:
            self.set_browser_visible(True, "https://www.sityea.com/exercises/")
        elif ui_type == UI_TYPES.EXERCISES:
            self.set_browser_visible(
                True, "https://www.sityea.com/workplace-setup/")
        else:
            self.set_browser_visible(False)

        self.ui_prev = self.ui_open
        self.ui_open = ui_type

    def __create_buttons(self):
        buttons = []

        buttons.append((
            np.array([30, 675]),
            np.array([160, 30]),
            None,
            lambda: self.show_ui(UI_TYPES.CALIBRATE)
        ))

        buttons.append((
            np.array([20, 87]),
            np.array([160, 25]),
            None,
            lambda: self.show_ui(UI_TYPES.DASHBOARD)
        ))

        buttons.append((
            np.array([20, 142]),
            np.array([160, 25]),
            None,
            lambda: self.show_ui(UI_TYPES.EXERCISES)
        ))

        buttons.append((
            np.array([20, 170]),
            np.array([160, 25]),
            None,
            lambda: self.show_ui(UI_TYPES.WORKSPACE)
        ))

        buttons.append((
            np.array([920, 90]),
            np.array([100, 25]),
            None,
            self.on_clear_history
        ))

        buttons.append((
            np.array([420, 525]),
            np.array([67, 17]),
            lambda: self.img_btn_on if self.config.TAKE_BREAK.NOTIFICATION_SOUND else self.img_btn_off,
            lambda: self.on_toggle_audio(self.config.TAKE_BREAK)
        ))

        buttons.append((
            np.array([660, 525]),
            np.array([67, 17]),
            lambda: self.img_btn_on if self.config.TAKE_BREAK.NOTIFICATION_DESKTOP else self.img_btn_off,
            lambda: self.on_toggle_notifications(self.config.TAKE_BREAK)
        ))

        buttons.append((
            np.array([385, 487]),
            np.array([20, 20]),
            None,
            lambda: self.on_minute_change(self.config.TAKE_BREAK, -1)
        ))

        buttons.append((
            np.array([447, 487]),
            np.array([20, 20]),
            None,
            lambda: self.on_minute_change(self.config.TAKE_BREAK, +1)
        ))

        buttons.append((
            np.array([420, 645]),
            np.array([67, 17]),
            lambda: self.img_btn_on if self.config.BAD_POSTURE.NOTIFICATION_SOUND else self.img_btn_off,
            lambda: self.on_toggle_audio(self.config.BAD_POSTURE)
        ))

        buttons.append((
            np.array([660, 645]),
            np.array([67, 17]),
            lambda: self.img_btn_on if self.config.BAD_POSTURE.NOTIFICATION_DESKTOP else self.img_btn_off,
            lambda: self.on_toggle_notifications(self.config.BAD_POSTURE)
        ))

        buttons.append((
            np.array([385, 607]),
            np.array([20, 20]),
            None,
            lambda: self.on_minute_change(self.config.BAD_POSTURE, -1)
        ))

        buttons.append((
            np.array([447, 607]),
            np.array([20, 20]),
            None,
            lambda: self.on_minute_change(self.config.BAD_POSTURE, +1)
        ))

        return buttons

    def draw_clickable_buttons(self, composite):
        frame = self.click_frame

        if not getattr(sys, "frozen", False):
            dbg_buffer = self.dbg_buffer
            dbg_image = self.dbg_image
            dbg_buffer[:] = 0

        for xy, wh, btn, _ in self.buttons:
            if btn is None:
                if not getattr(sys, "frozen", False):
                    dbg_buffer = cv2.rectangle(dbg_buffer, tuple(
                        xy), tuple(xy + wh), (255, 0, 0, 255))
            else:
                frame.paste(btn(), tuple(xy))

        composite = pilImage.composite(
            frame, composite, frame)

        if not getattr(sys, "frozen", False):
            composite = pilImage.composite(
                dbg_image, composite, dbg_image)

        return composite

    def on_click_canvas(self, event):
        x, y = event.x, event.y

        for xy, wh, _, callback in self.buttons:
            x1, y1 = xy
            x2, y2 = xy + wh

            if x < x1 or x > x2:
                continue
            if y < y1 or y > y2:
                continue
            if callback is None:
                continue

            callback()

            break

    def __create_elements(self):
        dpi = 100
        figCur = plt.figure(1, figsize=(938/dpi, 210/dpi),
                            dpi=dpi)
        figTtl = plt.figure(2, figsize=(210/dpi, 210/dpi),
                            dpi=dpi)
        canvas = tk.Canvas(self, bg="green", borderwidth=0,
                           highlightthickness=0)

        canvas.bind("<Button-1>", self.on_click_canvas)

        def create_prediction_delay():
            sv = tk.StringVar(value="%i" %
                              self.config.HISTORY.TIME_PREDICTION)
            sv.trace("w", lambda name, index, mode,
                     sv=sv: self.on_validate_number(sv, self.config.HISTORY, "TIME_PREDICTION", 2))
            ui_input = tk.Entry(
                self, textvariable=sv, width=3)

            return ui_input

        def create_take_break_input():
            sv = tk.StringVar(value="%i" %
                              self.config.TAKE_BREAK.NOTIFICATION_TIME)
            sv.trace("w", lambda name, index, mode,
                     sv=sv: self.on_validate_number(sv, self.config.TAKE_BREAK, "NOTIFICATION_TIME", 3))
            ui_input = tk.Entry(
                self, textvariable=sv, width=3)

            return ui_input

        def create_bad_posture_input():
            sv = tk.StringVar(value="%i" %
                              self.config.BAD_POSTURE.NOTIFICATION_TIME)
            sv.trace("w", lambda name, index, mode,
                     sv=sv: self.on_validate_number(sv, self.config.BAD_POSTURE, "NOTIFICATION_TIME", 3))
            ui_input = tk.Entry(
                self, textvariable=sv, width=3)

            return ui_input

        self.field_take_break = create_take_break_input()
        self.field_bad_posture = create_bad_posture_input()
        self.field_prediction = create_prediction_delay()

        self.browser = BrowserFrame(self)

        self.set_fields_visible(True)

        return (figCur, figTtl), canvas

    def set_browser_visible(self, is_visible, url=None):
        if is_visible:
            self.browser.place(x=250, y=125, width=930, height=550)
            self.browser.goto(url)
        else:
            self.browser.place_forget()

    def get_window_handle(self):
        if self.winfo_id() > 0:
            return self.winfo_id()
        else:
            raise Exception("Couldn't obtain window handle")

    def set_fields_visible(self, is_visible):
        if is_visible:
            self.field_take_break.place(x=412, y=487)
            self.field_bad_posture.place(x=412, y=607)
            self.field_prediction.place(x=1115, y=91)
        else:
            els = [
                self.field_take_break,
                self.field_bad_posture,
                self.field_prediction
            ]
            [el.place_forget() for el in els]

    def update_fields(self):
        def set_value(el, val):
            el.delete(0, "end")
            el.insert(0, val)

        set_value(self.field_take_break,
                  self.config.TAKE_BREAK.NOTIFICATION_TIME)
        set_value(self.field_bad_posture,
                  self.config.BAD_POSTURE.NOTIFICATION_TIME)
        set_value(self.field_prediction, self.config.HISTORY.TIME_PREDICTION)

    def on_validate_number(self, sv, object, key, max_length):
        previous_value = getattr(object, key)

        try:
            value = sv.get()

            if len(value) > max_length:
                raise ValueError()

            if value == "":
                return

            parsed_value = int(value)

            if parsed_value >= 0:
                previous_value = "%i" % parsed_value
                setattr(object, key, parsed_value)
                sv.set(previous_value)

                self.config.save()

        except ValueError:
            sv.set(previous_value)

    def on_clear_history(self):
        self.history_all[...] = 0
        self.save_history()

    def on_toggle_audio(self, section):
        section.NOTIFICATION_SOUND = not section.NOTIFICATION_SOUND
        self.config.save()

    def on_minute_change(self, section, value):
        section.NOTIFICATION_TIME = max(
            1, min(999, section.NOTIFICATION_TIME + value))

        self.update_fields()
        self.config.save()

    def on_toggle_notifications(self, section):
        section.NOTIFICATION_DESKTOP = not section.NOTIFICATION_DESKTOP
        self.config.save()

    def on_key_press(self, event):
        if event.char == "q":
            self.is_running = False

    def on_window_close(self):
        self.is_running = False

import os
import time
import hashlib
import platform
import numpy as np
import tkinter as tk

NORM_FONT = ("Verdana", 14)
CORRECT_PASSWORD = "20210309"
KEY_FILE = ".key"
ALLOWED_TIME = 60 * 60 * 24 * 30 * 3


class AppWankerProtect:
    def __init__(self):
        sys_info = platform.uname()
        sys_hash = sys_info.node + sys_info.system + sys_info.processor
        self.sys_hash = hashlib.sha1(sys_hash.encode("utf-8")).hexdigest()
        
    def initialize(self):
        self.popup = tk.Tk()
        self.popup.wm_title("Password")
        self.last_password = ""

        def create_fuck_off():
            frame_warning_delay = tk.Frame(self.popup)
            frame_warning_delay.grid(row=0, column=0)

            label_warning_delay = tk.Label(
                frame_warning_delay, text="Password:", font=NORM_FONT)
            label_warning_delay.grid(row=0, column=0)

            sv = tk.StringVar(value="")
            sv.trace("w", lambda name, index, mode,
                     sv=sv: self.on_validate(sv))
            input_warning_delay = tk.Entry(
                frame_warning_delay, textvariable=sv, width=64, font=NORM_FONT)
            input_warning_delay.grid(row=0, column=1)

            label_warning_delay_s = tk.Button(
                frame_warning_delay, text="Okay", command=self.popup.destroy, font=NORM_FONT)
            label_warning_delay_s.grid(row=0, column=2)

        create_fuck_off()

    def start(self):
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                sys_hash, timestamp = np.load(f)

            if sys_hash == self.sys_hash and float(timestamp) + ALLOWED_TIME > time.time():
                # self.popup.destroy()
                return True

            os.unlink(KEY_FILE)

        self.initialize()
        self.popup.mainloop()

        is_correct = self.last_password == CORRECT_PASSWORD

        if is_correct:
            with open(KEY_FILE, "wb") as f:
                np.save(f, (self.sys_hash, time.time()))

        return is_correct

    def on_validate(self, sv):
        previous_value = self.last_password

        try:
            value = sv.get()

            if len(value) > 40:
                raise ValueError()

            if value == "":
                return

            self.last_password = value

        except ValueError:
            sv.set(previous_value)

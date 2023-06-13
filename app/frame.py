import cv2
import numpy as np
from PIL import Image as pilImage


class AppFrame:
    def __init__(self):
        self.last_frames, self.max_frames = ["unknown"], 10

    def __update_frame(self, display_frame):
        display_shape = np.shape(display_frame)

        image_data = cv2.cvtColor(
            np.array(self.input_frame[0, ..., :3], dtype=np.float32), cv2.COLOR_BGR2RGB)

        image_shape = image_data.shape
        image_data = cv2.resize(
            image_data, (self.frame_width, self.frame_height))

        image_shape = image_data.shape

        y1 = self.frame_offset_height
        x1 = display_shape[1] - image_shape[1] - self.frame_offset_width
        y2, x2 = image_shape[0] + y1, image_shape[1] + x1

        display_frame[y1:y2, x1:x2] = image_data

        return display_frame

    def __get_framed_xy(self, image, frame_size, xy):
        width, height = frame_size

        frame = pilImage.new("RGBA", (width, height))
        frame.paste(image, xy)

        return frame

    def __get_framed(self, image, frame_size, keep_aspect=False):
        width, height = frame_size
        fr_aspect_ratio = self.frame_width / self.frame_height
        aspect_ratio = image.width / image.height if keep_aspect else fr_aspect_ratio
        
        image = image.resize(
            (round(self.frame_height * aspect_ratio), self.frame_height))
        frame = pilImage.new("RGBA", (width, height))

        y1 = self.frame_offset_height
        x1 = width - self.frame_width - self.frame_offset_width

        if keep_aspect:
            x1 = x1 - round(image.width * 0.5) + round(self.frame_width * 0.5)

        frame.paste(image, (x1, y1))

        return frame
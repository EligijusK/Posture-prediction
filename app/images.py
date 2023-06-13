import os
import cv2
import numpy as np
from PIL import Image as pilImage


class AppImages:
    def __init__(self, dirname):
        self.img_calibration, self.img_background, self.img_settings, \
            self.img_workspace, self.img_exercises, self.img_silhouette, \
            self.img_btn_on, self.img_btn_off = \
            self.__get_images(dirname)

    def __get_images(self, dirname):

        def read_image(path):
            print("reading image: '%s'" % path)
            image_data = AppImages.read_image(
                dirname, path, cv2.IMREAD_UNCHANGED)
            image_data = np.array(image_data * 255, dtype=np.uint8)
            image_data = cv2.cvtColor(image_data, cv2.COLOR_BGRA2RGBA)
            image_data = pilImage.fromarray(image_data)

            return image_data

        image_list = [
            "calibration.png",
            "background.png",
            "settings.png",
            "workspace.png",
            "exercises.png",
            "silhouette.png",
            "btn_on.png",
            "btn_off.png"
        ]
        images = [read_image(path) for path in image_list]
        images = [im.resize([int(v) for v in np.array(im.size) * 0.85])
                  for im in images]

        return images

    @staticmethod
    def read_image(dirname, path, flags=None):
        image_path = os.path.realpath("%s/images/%s" % (dirname, path))

        return (cv2.imread(image_path, flags) if flags else cv2.imread(image_path)) / 255

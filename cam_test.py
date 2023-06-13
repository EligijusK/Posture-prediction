
import cv2
import sys
import torch
import numpy as np
import pyrealsense2 as rs
from configs.args import args
import configs.config as cfg
from utils.network_bootstrap import get_network_constructor
from data.label_manager import LabelManager
from rs.pipeline import RSPipeLine
from utils.sys_colors import RED, BLUE, GREEN, RESET
from utils.image_to_points import image_to_points
# import open3d as o3d

cfg.TRAINING.USE_PREPROCESSED = False

height, width, _ = cfg.DATA.RESOLUTION.FRAME
man_labels = LabelManager(cfg.DATA.PATH_TAXONOMY)

Network = get_network_constructor(args.checkpoint, False)

network = Network(man_labels=man_labels,
                  checkpoint=args.checkpoint,
                  checkpoint_type=args.checkpoint_type
                  )

context = rs.context()
devices = context.query_devices()


# if len(devices) == 0:
#     print("%sNo RealSense device connected" % RED)
#     exit(0)

# dev = RSPipeLine(devices[0])
dev = RSPipeLine("RS_D435I_20210210_181932.bag")

print("%sDevice found: %s%s%s" % (BLUE, GREEN, dev.name, RESET))

dev.start()

matrix_K = dev.matrix_K
depth_scale = dev.depth_scale
depth_max = cfg.DATA.DEPTH.MAX

align_to = rs.stream.color
align = rs.align(align_to)

combined_frame = np.zeros([height, width * 2, 3])
frame_count, every_frames = 0, 0

label, col_background, col_foreground = "unknown", (0, 0, 0), (255, 255, 255)

while True:
    try:
        index = 0
        frame = dev.wait_for_frames(5000)
        frame = align.process(frame)

        color, depth = frame.get_color_frame(), frame.get_depth_frame()

        data_color = np.array(color.get_data())
        data_depth = np.array(
            depth.get_data(), dtype=np.float)

        frame = np.concatenate(
            [data_color / 255, data_depth[..., np.newaxis]], axis=-1)
        points = image_to_points(frame, matrix_K, depth_scale, depth_max)

        # points = points[0::2][0::2][0::2][0::2][0::2]

        if frame_count > every_frames:
            # indices = np.random.choice(points.shape[0], cfg.MODEL.IN_POINTS)
            # indices.sort()
            # points = points[indices]
            # points = np.random.rand(cfg.MODEL.IN_POINTS, 6)
            t_in = torch.tensor(points).unsqueeze(0)
            t_out = network.predict(t_in)
            prediction = t_out[0].cpu().numpy()

            label, col_background, col_foreground = man_labels.get_label(
                prediction)
            frame_count = 0
        else:
            frame_count = frame_count + 1

        data_color = cv2.cvtColor(data_color, cv2.COLOR_RGB2BGR) / 255
        data_depth = np.array(
            data_depth / data_depth.max() * 255, dtype=np.uint8)
        data_depth = cv2.applyColorMap(data_depth, cv2.COLORMAP_JET) / 255

        combined_frame[height*index:height*(index+1), :width, :] = data_color
        combined_frame[height*index:height*(index+1), width:, :] = data_depth

        combined_frame = cv2.putText(combined_frame, label, (height, 25), cv2.FONT_HERSHEY_SIMPLEX,
                                     1, col_background, 3, cv2.LINE_AA)
        combined_frame = cv2.putText(combined_frame, label, (height, 25), cv2.FONT_HERSHEY_SIMPLEX,
                                     1, col_foreground, 1, cv2.LINE_AA)

        cv2.imshow("Realsense", combined_frame)
        cv2.waitKey(16)
    except Exception as ex:
        print(ex)

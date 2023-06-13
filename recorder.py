import os
import cv2
import re
import pyrealsense2 as rs
import numpy as np
from datetime import datetime
from rs.config import width, height
from rs.pipeline import RSPipeLine
from utils.get_asset import get_asset_path

context = rs.context()
devices = context.query_devices()
out_dir = os.path.normpath(os.path.expanduser("~/Desktop/outputs")) \
    if re.search("\\\\WindowsApps", get_asset_path()) \
    else get_asset_path("outputs")
dev_pipelines = [RSPipeLine(dev) for dev in devices]

# Start streaming
align_to = rs.stream.color
align = rs.align(align_to)

is_running = True
is_recording = False
[pipeline.start() for pipeline in dev_pipelines]


def toggle_recording():
    global is_recording

    is_recording = not is_recording

    if is_recording:
        os.makedirs(out_dir, exist_ok=True)
        cur_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    for pipeline in dev_pipelines:
        pipeline.stop()

        if is_recording:
            pipeline.start_recording(out_dir, cur_time)
        else:
            pipeline.start()


combined_frame = np.zeros([height * len(dev_pipelines), width * 2, 3])


def await_frame(pipeline, index):
    frame = pipeline.wait_for_frames()
    frame = align.process(frame)

    color, depth = frame.get_color_frame(), frame.get_depth_frame()

    data_color = np.array(color.get_data())
    data_depth = np.array(depth.get_data(), dtype=np.float)

    data_color = cv2.cvtColor(data_color, cv2.COLOR_BGR2RGB) / 255
    data_depth = np.array(
        data_depth / data_depth.max() * 255, dtype=np.uint8)
    data_depth = cv2.applyColorMap(data_depth, cv2.COLORMAP_JET) / 255

    combined_frame[height*index:height*(index+1), :width, :] = data_color
    combined_frame[height*index:height*(index+1), width:, :] = data_depth


try:
    while is_running:
        [await_frame(pipeline, i) for i, pipeline in enumerate(dev_pipelines)]

        combined_frame = cv2.putText(combined_frame, "Colorspace", (height >> 1, 25), cv2.FONT_HERSHEY_SIMPLEX,
                                     1, (0, 0, 0), 3, cv2.LINE_AA)
        combined_frame = cv2.putText(combined_frame, "Colorspace", (height >> 1, 25), cv2.FONT_HERSHEY_SIMPLEX,
                                     1, (255, 255, 255), 1, cv2.LINE_AA)
        combined_frame = cv2.putText(combined_frame, "Depth", (height << 1, 25), cv2.FONT_HERSHEY_SIMPLEX,
                                     1, (0, 0, 0), 3, cv2.LINE_AA)
        combined_frame = cv2.putText(combined_frame, "Depth", (height << 1, 25), cv2.FONT_HERSHEY_SIMPLEX,
                                     1, (255, 255, 255), 1, cv2.LINE_AA)

        if not is_recording:
            combined_frame = cv2.putText(combined_frame, "Recording [off]", (height, 25), cv2.FONT_HERSHEY_SIMPLEX,
                                         1, (0, 0, 0), 3, cv2.LINE_AA)
            combined_frame = cv2.putText(combined_frame, "Recording [off]", (height, 25), cv2.FONT_HERSHEY_SIMPLEX,
                                         1, (0, 0, 255), 1, cv2.LINE_AA)
        else:
            combined_frame = cv2.putText(combined_frame, "Recording [on]", (height, 25), cv2.FONT_HERSHEY_SIMPLEX,
                                         1, (0, 0, 0), 3, cv2.LINE_AA)
            combined_frame = cv2.putText(combined_frame, "Recording [on]", (height, 25), cv2.FONT_HERSHEY_SIMPLEX,
                                         1, (0, 255, 0), 1, cv2.LINE_AA)

        cv2.imshow("Realsense input", combined_frame)
        key = cv2.waitKey(1)

        if key == ord("q"):
            is_running = False
        elif key == 0xBE or key == ord("r"):  # F1
            toggle_recording()
except Exception as ex:
    print(ex)
finally:
    [pipeline.stop() for pipeline in dev_pipelines]

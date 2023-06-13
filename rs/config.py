import pyrealsense2 as rs
import configs.config as config

width, height, framerate = config.DATA.RESOLUTION.FRAME[1], config.DATA.RESOLUTION.FRAME[0], 30


def create_config(*, width=width, height=height, framerate=framerate, device_id=None):

    config = rs.config()

    # if device_id is not None:
    #     config.enable_device(device_id)

    # config.enable_stream(rs.stream.depth, width, height,
    #                      rs.format.z16, framerate)
    # config.enable_stream(rs.stream.color, width, height,
    #                      rs.format.rgb8, framerate)

    config.enable_stream(rs.stream.depth, width, height)
    config.enable_stream(rs.stream.color, width, height)

    return config


def create_playback_config(path, *, width=width, height=height, framerate=framerate):
    config = create_config(width=width, height=height, framerate=framerate)
    config.enable_device_from_file(path, True)

    return config


def create_record_config(path, *, width=width, height=height, framerate=framerate):
    config = create_config(width=width, height=height, framerate=framerate)

    config.enable_record_to_file(path)

    return config

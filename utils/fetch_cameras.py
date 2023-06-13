import os
import cv2
import asyncio
import platform
import subprocess

if platform.system() == "Windows":
    import winrt.windows.devices.enumeration as windows_devices


async def get_camera_information_for_windows():
    return await windows_devices.DeviceInformation.find_all_async(windows_devices.DeviceClass.VIDEO_CAPTURE)


async def fetch_all_cameras():
    cameras = []
    platform_name = platform.system()

    if platform_name == "Windows":
        win_camlist = await get_camera_information_for_windows()

        for cam_idx, cam in enumerate(win_camlist):
            try:
                capture = cv2.VideoCapture(cam_idx)
                if capture.read()[0]:
                    cam_name = cam.name.replace("\n", "")
                    capture.release()
                    cameras.append({"camera_index": cam_idx,
                                    "camera_name": cam_name})
            except:
                continue

    if platform_name == "Linux":
        dev_list = "/sys/class/video4linux"

        if not os.path.exists(dev_list):
            return cameras

        _, lnx_camlist, _ = next(os.walk(dev_list))

        for dir_cam in lnx_camlist:
            with open("%s/%s/index" % (dev_list, dir_cam), "r") as f:
                cam_idx = int(f.readline())

            try:
                capture = cv2.VideoCapture(cam_idx)
                if capture.read()[0]:
                    with open("%s/%s/name" % (dev_list, dir_cam), "r") as f:
                        cam_name = f.readline().replace("\n", "")
                    capture.release()

                    cameras.append({"camera_index": cam_idx,
                                    "camera_name": cam_name})
                else:
                    print("Camera failed: '%s/%s/index'" % (dev_list, dir_cam))
            except:
                continue

    return cameras


if __name__ == "__main__":
    try:
        print(asyncio.run(fetch_all_cameras()))
    except asyncio.CancelledError as ex:
        exit(0)

import os
import cv2
import asyncio
import platform
import subprocess

if platform.system() == "Windows":
    import winsdk.windows.devices.enumeration as windows_devices


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

    if platform_name == "Darwin":

        darw_camListName2 = subprocess.run('system_profiler SPCameraDataType | grep "^    [^ ]" | sed "s/    //" | sed "s/://"', capture_output=True, text=True, shell=True)
        cameraNameoutput = darw_camListName2.stdout
        cameraNameoutput = cameraNameoutput[:-1]
        camera_listNames2 = cameraNameoutput.split("\n")

        darw_camListIndex = subprocess.run('system_profiler SPCameraDataType | grep "^     " | sed -n "n;p" | sed "s/      //" | sed "s/://" | cut -d " " -f3-3', capture_output=True, text=True, shell=True)
        cameraIdOutput = darw_camListIndex.stdout
        cameraIdOutput = cameraIdOutput[:-1]
        camera_listIndex = cameraIdOutput.split("\n")
        n = len(camera_listIndex)
        for i in range(n):
            swap = False
            for j in range(0, n - i - 1):

                firstElement = int(camera_listIndex[j], 16)
                secondElement = int(camera_listIndex[j + 1], 16)
                if firstElement > secondElement:
                    camera_listIndex[j], camera_listIndex[j + 1] = camera_listIndex[j + 1], camera_listIndex[j]
                    camera_listNames2[j], camera_listNames2[j + 1] = camera_listNames2[j + 1], camera_listNames2[j]
                    swap = True
            if swap == False:
                break

        for index, camera_name in zip(camera_listIndex, camera_listNames2):
            print(camera_name + " - " + index)

        index = 0
        for dir_cam in camera_listNames2:
            try:
                capture = cv2.VideoCapture(index)
                capture.open(index)
                if capture.read()[0]:
                    cam_name = dir_cam
                    capture.release()
                    cameras.append({"camera_index": index,
                                    "camera_name": cam_name})
                index += 1
            except Exception as err:
                print(err)
                continue



    return cameras


if __name__ == "__main__":
    try:
        print(asyncio.run(fetch_all_cameras()))
    except asyncio.CancelledError as ex:
        exit(0)

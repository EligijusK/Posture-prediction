class NoDeviceException(Exception):
    def __init__(self):
        super().__init__("No Realsense devices connected.")


class USB30Exception(Exception):
    def __init__(self):
        super().__init__("At least USB 3.0 connection is required.")

class DevInUseException(Exception):
    def __init__(self):
        super().__init__("Device is already in use.")

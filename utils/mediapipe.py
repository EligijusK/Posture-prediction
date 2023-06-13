import numpy as _np


class _StubLandmark:
    def __init__(self, lm):
        self.x = lm[0]
        self.y = lm[1]
        self.z = lm[2]
        self.visibility = lm[3] if len(lm) >= 4 else 1
        self.presence = lm[4] if len(lm) >= 5 else 1

    def HasField(self, field):
        return False


class _StubLandmarks():
    def __init__(self, landmarks):
        self.landmark = [_StubLandmark(lm) for lm in landmarks]


def landmarks2numpy(landmarks):
    return _np.array([[lm.x, lm.y, lm.z, lm.visibility] for lm in landmarks], dtype=_np.float32)


def numpy2landmarks(numpy):
    return _StubLandmarks(numpy)

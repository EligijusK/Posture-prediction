import numpy as _np
from enum import Enum as _enum
import mediapipe as _mp

landmarks = _mp.solutions.pose.PoseLandmark


class Joints(_enum):
    CHEST = 0
    HIP_BASE = 1

    HEAD_BASE = 2
    HEAD_LEFT = 3
    HEAD_RIGHT = 4

    SHOULDER_LEFT = 5
    ELBOW_LEFT = 6
    WRIST_LEFT = 7

    SHOULDER_RIGHT = 8
    ELBOW_RIGHT = 9
    WRIST_RIGHT = 10

    HIP_LEFT = 11
    KNEE_LEFT = 12
    FOOT_LEFT = 13

    HIP_RIGHT = 14
    KNEE_RIGHT = 15
    FOOT_RIGHT = 16


_REVERSE_Joints = [j.name for j in Joints]
_CONNECTIONS = [
    [Joints.CHEST, Joints.HIP_BASE],

    [Joints.HIP_BASE, Joints.HIP_LEFT],
    # [Joints.HIP_LEFT, Joints.KNEE_LEFT],
    # [Joints.KNEE_LEFT, Joints.FOOT_LEFT],

    [Joints.HIP_BASE, Joints.HIP_RIGHT],
    # [Joints.HIP_RIGHT, Joints.KNEE_RIGHT],
    # [Joints.KNEE_RIGHT, Joints.FOOT_RIGHT],

    [Joints.CHEST, Joints.SHOULDER_LEFT],
    [Joints.SHOULDER_LEFT, Joints.ELBOW_LEFT],
    [Joints.ELBOW_LEFT, Joints.WRIST_LEFT],

    [Joints.CHEST, Joints.SHOULDER_RIGHT],
    [Joints.SHOULDER_RIGHT, Joints.ELBOW_RIGHT],
    [Joints.ELBOW_RIGHT, Joints.WRIST_RIGHT],

    [Joints.CHEST, Joints.HEAD_BASE],
    [Joints.HEAD_BASE, Joints.HEAD_LEFT],
    [Joints.HEAD_LEFT, Joints.HEAD_RIGHT],
    [Joints.HEAD_RIGHT, Joints.HEAD_BASE]
]

def convert_to_screenspace(v, w, h):
    x, y = v[0:2]
    x_px = min(_np.floor(x * w), w - 1)
    y_px = min(_np.floor(y * h), h - 1)

    return _np.array([x_px, y_px], dtype=_np.int32)


class Skeleton:
    CHEST = None
    HIP_BASE = None
    HEAD_BASE = None
    HEAD_LEFT = None
    HEAD_RIGHT = None
    SHOULDER_LEFT = None
    ELBOW_LEFT = None
    WRIST_LEFT = None
    SHOULDER_RIGHT = None
    ELBOW_RIGHT = None
    WRIST_RIGHT = None
    HIP_LEFT = None
    KNEE_LEFT = None
    FOOT_LEFT = None
    HIP_RIGHT = None
    KNEE_RIGHT = None
    FOOT_RIGHT = None

    def __init__(self):

        for j in Joints:
            setattr(self, j.name, _np.zeros(3, dtype=_np.float32))

    def __getitem__(self, index):
        return self[index.value] \
            if type(index) == Joints \
            else getattr(self, _REVERSE_Joints[index])

    def copy_state(self):
        return _np.array([self[j.value] for j in Joints], dtype=_np.float32)

    def fetch_pose(self, w, h):
        return [convert_to_screenspace(self[j.value], w, h).tolist() for j in Joints]

    # def draw(self, image, *, line_color=(0, 255, 0), line_thickness=2, joint_color=(0, 0, 255), joint_radius=2):
    #     h, w, _ = image.shape

    #     for j1, j2 in _CONNECTIONS:
    #         v1, v2 = self[j1.value], self[j2.value]
    #         p1 = tuple(convert_to_screenspace(v1, w, h).tolist())
    #         p2 = tuple(convert_to_screenspace(v2, w, h).tolist())

    #         _cv2.line(image, p1, p2, line_color, line_thickness)

    #     for j in Joints:
    #         v = self[j.value]
    #         p = tuple(convert_to_screenspace(v, w, h).tolist())

    #         _cv2.circle(image, p, joint_radius, joint_color, line_thickness)

    def update(self, mp_skeleton):

        LEFT_SHOULDER = mp_skeleton[landmarks.LEFT_SHOULDER]
        RIGHT_SHOULDER = mp_skeleton[landmarks.RIGHT_SHOULDER]
        CHEST = (LEFT_SHOULDER + RIGHT_SHOULDER) * 0.5

        LEFT_HIP = mp_skeleton[landmarks.LEFT_HIP]
        RIGHT_HIP = mp_skeleton[landmarks.RIGHT_HIP]
        HIP_BASE = (LEFT_HIP + RIGHT_HIP) * 0.5

        LEFT_ELBOW = mp_skeleton[landmarks.LEFT_ELBOW]
        RIGHT_ELBOW = mp_skeleton[landmarks.RIGHT_ELBOW]

        LEFT_WRIST = mp_skeleton[landmarks.LEFT_WRIST]
        RIGHT_WRIST = mp_skeleton[landmarks.RIGHT_WRIST]

        LEFT_KNEE = mp_skeleton[landmarks.LEFT_KNEE]
        RIGHT_KNEE = mp_skeleton[landmarks.RIGHT_KNEE]

        LEFT_HEEL = mp_skeleton[landmarks.LEFT_HEEL]
        RIGHT_HEEL = mp_skeleton[landmarks.RIGHT_HEEL]

        LEFT_EYE = mp_skeleton[landmarks.LEFT_EAR]
        RIGHT_EYE = mp_skeleton[landmarks.RIGHT_EAR]

        MOUTH_LEFT = mp_skeleton[landmarks.MOUTH_LEFT]
        MOUTH_RIGHT = mp_skeleton[landmarks.MOUTH_RIGHT]
        MOUTH_CENTER = (MOUTH_LEFT + MOUTH_RIGHT) * 0.5

        self.CHEST[...] = CHEST[0:3]
        self.HIP_BASE[...] = HIP_BASE[0:3]
        self.HEAD_BASE[...] = MOUTH_CENTER[0:3]
        self.HEAD_LEFT[...] = LEFT_EYE[0:3]
        self.HEAD_RIGHT[...] = RIGHT_EYE[0:3]
        self.SHOULDER_LEFT[...] = LEFT_SHOULDER[0:3]
        self.ELBOW_LEFT[...] = LEFT_ELBOW[0:3]
        self.WRIST_LEFT[...] = LEFT_WRIST[0:3]
        self.SHOULDER_RIGHT[...] = RIGHT_SHOULDER[0:3]
        self.ELBOW_RIGHT[...] = RIGHT_ELBOW[0:3]
        self.WRIST_RIGHT[...] = RIGHT_WRIST[0:3]
        self.HIP_LEFT[...] = LEFT_HIP[0:3]
        self.KNEE_LEFT[...] = LEFT_KNEE[0:3]
        self.FOOT_LEFT[...] = LEFT_HEEL[0:3]
        self.HIP_RIGHT[...] = RIGHT_HIP[0:3]
        self.KNEE_RIGHT[...] = RIGHT_KNEE[0:3]
        self.FOOT_RIGHT[...] = RIGHT_HEEL[0:3]

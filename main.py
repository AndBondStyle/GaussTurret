from server import Server
from stream import *
from motion import *
import numpy as np
import time
import cv2


STREAM = CVStream            # Stream handler
WIDTH = 320                  # Frame width (None = max)
HEIGHT = 240                 # Frame height (None = max)
FPS = None                   # Stream FPS (None = max)
FLIP = None                  # Frame flip mode (0 = H | 1 = V | -1 = both | None = no flip)

MOTION = OPiMotion           # Motion handler
MOTION_PINS = {
    'ENABLE': 11,            # A4988 enable pin
    'STEP': 3,               # A4988 step pin
    'DIR': 5,                # A4988 dir pin
    'PWM': 7,                # Servo PWM pin
    'FIRE': 13,               # Fire pin
}
MOTION_PARAMS = {
    'SPEED': 30,             # Normal speed (steps per second)
    'SLOWSPEED': 5,          # Slow speed (steps per second)
    'REVERSE': False,        # Reverse direction
    'REVOLUTION': 320,       # Steps per full revolution
    'ROTATION_RANGE': 0,     # Rotation range limit (0 = no limits)
    'SLEEP_TIMEOUT': 5,      # Time to wait before disabling stepper
    'FIRE_PULSE': 0.1,       # Fire pulse length (seconds)
    'RECHARGE_TIME': 5,      # Aka minimal time between shots
    'MIN_PWM': 0,            # Min servo PWM
    'MAX_PWM': 50,           # Max servo PWM
}

ARMING_TIMEOUT = 5                         # Time to wait before arming
ARMING_TEXT_FONT = cv2.FONT_HERSHEY_PLAIN  # Arming status text param: font
ARMING_TEXT_FONT_SCALE = 1.5               # Arming status text param: scale
ARMING_TEXT_POS = (5, 20)                  # Arming status text param: position

FACE_HAAR_PATH = 'data/face_default.xml'   # Path to haar cascade file (for face detection)
FACE_SCALE_FACTOR = 1.1                    # Face detection param: scaleFactor
FACE_MIN_NEIGHBOURS = 5                    # Face detection param: minNeighbours
FACE_MIN_SIZE = (50, 50)                 # Face detection param: minSize
FACE_FLAGS = cv2.CASCADE_SCALE_IMAGE       # Face detection param: flags

CAMERA_MATRIX = np.array([                 # Camera matrix coefficients (calibration result)
    [544.70473098, 0.0, 177.46434358],
    [0.0, 547.27945612, 146.11552008],
    [0.0, 0.0, 1.0],
])
CAMERA_DISTORTION = np.array([             # Camera distortion coefficients (calibration result)
    5.37779339e-01,
    9.15783371e+00,
    4.65765217e-03,
    -1.17879940e-02,
    -1.22638201e+02,
])

MARKERS_DICT = cv2.aruco.DICT_6X6_50       # Aruco markers dict
MARKER_LENGTH = 33                         # Marker side length (mm)


class Core(BaseStream):
    def __init__(self):
        super().__init__()
        self.stream = STREAM(width=WIDTH, height=HEIGHT, fps=FPS)
        self.motion = MOTION(MOTION_PINS, MOTION_PARAMS)
        self.server = Server(self)
        self.event = self.stream.subscribe()

        self.aruco_dict = cv2.aruco.Dictionary_get(MARKERS_DICT)
        self.face_cascade = cv2.CascadeClassifier(FACE_HAAR_PATH)
        self.draw_arming_text = lambda img, text, color: cv2.putText(
            img, text, ARMING_TEXT_POS, ARMING_TEXT_FONT, ARMING_TEXT_FONT_SCALE, color, 1
        )
        self.last_face_time = time.time()

        self.frame = None
        self.gray = None
        self.markers = []
        self.faces = []

    def process_markers(self):
        corners, ids, _ = cv2.aruco.detectMarkers(self.gray, self.aruco_dict)
        self.markers = []
        if ids is None: return
        self.markers = [{'id': int(i[0]), 'corners': c.astype(int).tolist()} for c, i in zip(corners, ids)]
        rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(corners, MARKER_LENGTH, CAMERA_MATRIX, CAMERA_DISTORTION)
        for i in self.markers: i.update(rvec=rvec.tolist(), tvec=tvec.tolist())
        cv2.aruco.drawDetectedMarkers(self.frame, corners, borderColor=(0, 0, 255))

    def process_faces(self):
        faces = self.face_cascade.detectMultiScale(
            self.gray,
            scaleFactor=FACE_SCALE_FACTOR,
            minNeighbors=FACE_MIN_NEIGHBOURS,
            minSize=FACE_MIN_SIZE,
            flags=FACE_FLAGS
        )
        self.faces = [] if not len(faces) else faces.tolist()

        if self.faces:
            self.motion.armed = False
            self.last_face_time = time.time()
        elif time.time() - self.last_face_time >= ARMING_TIMEOUT:
            self.motion.armed = True

        for (x, y, w, h) in self.faces: cv2.rectangle(self.frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
        if self.motion.armed: self.draw_arming_text(self.frame, 'ARMED', (0, 0, 255))
        elif self.faces: self.draw_arming_text(self.frame, 'DISARMED', (0, 255, 0))
        else: self.draw_arming_text(self.frame, 'ARMING', (0, 200, 255))

    def stop(self):
        self.stopped = True
        self.event.set()
        self.join()

    def run(self):
        self.stream.start()
        self.motion.start()
        self.server.start()

        while not self.stopped:
            self.event.wait()
            if self.stopped: break
            self.event.clear()

            frame = self.stream.frame
            if frame is None: continue
            if FLIP is not None: frame = cv2.flip(frame, FLIP)
            self.gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.frame = cv2.cvtColor(self.gray, cv2.COLOR_GRAY2BGR)

            self.process_markers()
            self.process_faces()
            self.notify()

        print('[CORE] STOPPING STREAM THREAD...')
        self.stream.stop()
        print('[CORE] STOPPING MOTION THREAD...')
        self.motion.stop()
        print('[CORE] STOPPING SERVER THREAD...')
        self.server.stop()
        print('[CORE] TERMINATED')


if __name__ == '__main__':
    core = Core()
    core.start()
    input('[CORE] ENTER TO TERMINATE\n\n')
    core.stop()

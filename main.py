from server import Server
from stream import *
from motion import *
import cv2


STREAM = FakeStream          # Stream handler
WIDTH = 320                  # Frame width (None = max)
HEIGHT = 240                 # Frame height (None = max)
FPS = None                   # Stream FPS (None = max)
FLIP = None                  # Frame flip mode (0 = H | 1 = V | -1 = both | None = no flip)

MOTION = BaseMotion          # Motion handler
PINS = {
    'ENABLE': 0,             # A4988 enable pin
    'STEP': 0,               # A4988 step pin
    'DIR': 0,                # A4988 dir pin
    'PWM': 0,                # Servo PWM pin
    'FIRE': 0,               # Fire pin
}
PARAMS = {
    'SPEED': 10,             # Normal speed (steps per second)
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

ARMING_TIMEOUT = 5                   # Time to wait before arming
HAAR_PATH = 'data/face_default.xml'  # Path to haar cascade file


class Core(BaseStream):
    def __init__(self):
        super().__init__()
        self.stream = STREAM(width=WIDTH, height=HEIGHT, fps=FPS)
        self.motion = MOTION(PARAMS)
        self.server = Server(self)
        self.event = self.stream.subscribe()

        self.aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_250)
        self.face_cascade = cv2.CascadeClassifier(HAAR_PATH)

        self.frame = None
        self.gray = None
        self.markers = []
        self.faces = []

    def process_markers(self):
        corners, ids, rejected = cv2.aruco.detectMarkers(self.gray, self.aruco_dict)
        # TODO: Prettify data
        # TODO: Custom draw
        self.frame = cv2.aruco.drawDetectedMarkers(self.frame, corners)

    def process_faces(self):
        faces = self.face_cascade.detectMultiScale(
            self.gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        # TODO: Prettify data
        # TODO: Draw

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

        print('STOPPING STREAM THREAD...')
        self.stream.stop()
        print('STOPPING MOTION THREAD...')
        self.motion.stop()
        print('STOPPING SERVER THREAD...')
        self.server.stop()
        print('TERMINATED')


if __name__ == '__main__':
    core = Core()
    core.start()
    input('ENTER TO TERMINATE\n\n')
    core.stop()

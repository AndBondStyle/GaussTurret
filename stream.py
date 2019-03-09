# Raspberry Pi | PyPI: picamera
try:
    from picamera.array import PiRGBArray
    from picamera import PiCamera
except ImportError: pass

from threading import Thread, Event
from time import sleep
import cv2

__all__ = [
    'BaseStream',
    'RPiStream',
    'CVStream',
    'FakeStream'
]


class BaseStream(Thread):
    def __init__(self):
        super().__init__()
        self.frame = None
        self.stopped = False
        self.events = []

    def subscribe(self):
        event = Event()
        self.events.append(event)
        return event

    def notify(self):
        for event in self.events:
            event.set()

    def stop(self):
        self.stopped = True
        self.join()


class RPiStream(BaseStream):
    def __init__(self, width=None, height=None, fps=None):
        super().__init__()
        resolution = (width, height) if width and height else PiCamera.MAX_RESOLUTION
        framerate = fps or PiCamera.MAX_FRAMERATE
        self.camera = PiCamera(resolution=resolution, framerate=framerate)
        self.capture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.capture, format='bgr', use_video_port=True)

    def run(self):
        while not self.stopped:
            framedata = next(self.stream)
            self.frame = framedata.array
            self.capture.truncate(0)
            self.notify()

        self.stream.close()
        self.capture.close()
        self.camera.close()


class CVStream(BaseStream):
    def __init__(self, width=None, height=None, fps=None):
        super().__init__()
        self.capture = cv2.VideoCapture(0)
        if width: self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        if height: self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if fps: self.capture.set(cv2.CAP_PROP_FPS, fps)

    def run(self):
        while not self.stopped:
            ok, frame = self.capture.read()
            if not ok: continue
            self.frame = frame
            self.notify()


class FakeStream(BaseStream):
    def __init__(self, width=None, height=None, fps=None):
        super().__init__()
        self.fps = fps or 10
        self.image = cv2.imread('dog.jpg')
        if width and height: self.image = cv2.resize(self.image, (width, height))

    def run(self):
        while not self.stopped:
            self.image = cv2.rotate(self.image, cv2.ROTATE_90_CLOCKWISE)
            self.frame = self.image
            self.notify()
            sleep(1 / self.fps)

try:
    from picamera.array import PiRGBArray
    from picamera import PiCamera
except:
    # Mock classes to make everything work without picamera
    PiRGBArray = lambda *args, **kwargs: None
    PiCamera = type('PiCamera', (), {
        'MAX_RESOLUTION': None,
        'MAX_FRAMERATE': None,
        '__init__': lambda *args, **kwargs: None
    })

from threading import Thread, Event
from time import sleep
import cv2


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


class PiStream(BaseStream):
    def __init__(self, resolution=PiCamera.MAX_RESOLUTION, framerate=PiCamera.MAX_FRAMERATE):
        super().__init__()
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
    def __init__(self):
        super().__init__()
        self.capture = cv2.VideoCapture(0)

    def run(self):
        while not self.stopped:
            ok, frame = self.capture.read()
            if not ok: continue
            self.frame = frame
            self.notify()
            sleep(0.1)


class FakeStream(BaseStream):
    def __init__(self):
        super().__init__()
        self.image = cv2.imread('test.jpg')

    def run(self):
        while not self.stopped:
            self.image = cv2.rotate(self.image, cv2.ROTATE_90_CLOCKWISE)
            self.frame = self.image
            self.notify()
            sleep(0.1)

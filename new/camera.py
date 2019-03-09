from multiprocessing import Process, Value, Event
from new.common import CameraConfig
import numpy as np
import cv2


class Camera(Process):
    frame = None
    event = None


    def __init__(self, config=None):
        super().__init__()
        self.capture = cv2.VideoCapture(0)
        self.config = CameraConfig.from_capture(self.capture)
        if config: self.config.update(config)
        self.config.apply(self.capture)

    def run(self):
        pass

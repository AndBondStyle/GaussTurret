import multiprocessing as mp
import numpy as np
import ctypes
import cv2


class FrameWrapper:
    def __init__(self, width=None, height=None, fps=None):
        self.width = width
        self.height = height
        self.fps = fps

    @staticmethod
    def from_capture(capture):
        width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = capture.get(cv2.CAP_PROP_FPS)
        return FrameWrapper(width, height, fps)

    def update(self, other):
        self.width = other.width or self.width
        self.height = other.height or self.height
        self.fps = other.fps or self.fps

    def apply(self, capture):
        if self.width: capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        if self.height: capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if self.fps: capture.set(cv2.CAP_PROP_FPS, self.fps)

    def dumpframe(self, frame): return frame.tobytes()

    def loadframe(self, data):
        frame = np.frombuffer(data)
        frame = frame.reshape((self.width, self.height))
        return frame

import multiprocessing as mp
import numpy as np
import ctypes
import time
import cv2

width, height = 200, 200


class BaseStream(mp.Process):
    def __init__(self):
        super().__init__()
        self.frame = None
        self.stopped = False
        self.events = []

    def subscribe(self):
        event = mp.Event()
        self.events.append(event)
        return event

    def notify(self):
        for event in self.events:
            event.set()

    def stop(self):
        self.stopped = True
        self.join()


class FakeStream(BaseStream):
    def __init__(self, buffer):
        super().__init__()
        self.image = cv2.imread('dog.jpg')
        self.buffer = buffer

    def run(self):
        self.frame = np.ctypeslib.as_array(self.buffer.get_obj())
        self.frame = self.frame.reshape((height, width, 3))

        while True:  # TODO: FIX
            self.image = cv2.rotate(self.image, cv2.ROTATE_90_CLOCKWISE)
            np.copyto(self.frame, self.image)
            self.notify()
            time.sleep(0.1)


if __name__ == '__main__':
    from server import Server

    buffer = mp.Array(ctypes.c_uint8, width * height * 3)
    # frame = np.ctypeslib.as_array(buffer.get_obj())
    # frame = frame.reshape((height, width, 3))

    stream = FakeStream(buffer)
    server = Server(buffer, stream.subscribe())
    stream.start()
    server.start()

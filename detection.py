from server import StreamServer
from motion import Motion
from camera import *
import numpy as np
import cv2


class ArucoDetector(BaseStream):
    def __init__(self, source):
        super().__init__()
        self.source = source
        self.motion = Motion()
        self.steps_per_pixel = 1 / 20
        self.threshold = 10
        self.width = 480  # TODO: FIX

    def stop(self):
        self.source.stop()
        self.motion.stop()
        super().stop()

    def run(self):
        self.source.start()
        self.motion.start()
        event = self.source.subscribe()
        dataset = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_250)
        parameters = cv2.aruco.DetectorParameters_create()

        while not self.stopped:
            # event.wait(1)
            # event.clear()
            frame = self.source.frame
            if frame is None: continue
            frame = cv2.flip(frame, -1)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, rejected = cv2.aruco.detectMarkers(gray, dataset, parameters=parameters)
            # frame = cv2.aruco.drawDetectedMarkers(frame, corners)
            ids = ids if ids is not None else [[]]
            zero = [i for i, x in enumerate(ids[0]) if x == 0]
            if zero:
                index = zero[0]
                corners = corners[index][0]
                center = tuple(np.mean(corners, axis=0).astype(int))
                cv2.circle(frame, center, 2, (0, 0, 255), -1)
                cv2.putText(frame, str(center[0]), center, cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255))

                delta = self.width / 2 - center[0]
                if abs(delta) >= self.threshold:
                    self.motion.steps = round(delta * self.steps_per_pixel)

            self.frame = frame
            self.notify()


if __name__ == '__main__':
    stream = CVStream()
    detector = ArucoDetector(stream)
    server = StreamServer(detector)
    detector.start()
    server.start()
    print('SERVER READY - ENTER TO TERMINATE')
    input()
    detector.stop()
    server.stop()

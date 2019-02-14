from server import StreamServer
from camera import *
import cv2


class ArucoDetector(BaseStream):
    def __init__(self, source):
        super().__init__()
        self.source = source

    def stop(self):
        self.source.stop()
        super().stop()

    def run(self):
        event = self.source.subscribe()
        dataset = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
        parameters = cv2.aruco.DetectorParameters_create()

        while not self.stopped:
            event.wait(1)
            event.clear()
            frame = self.source.frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            corners, ids, rejected = cv2.aruco.detectMarkers(gray, dataset, parameters=parameters)
            frame = cv2.aruco.drawDetectedMarkers(frame, corners, ids=ids)

            self.frame = frame
            self.notify()


if __name__ == '__main__':
    stream = CVStream()
    detector = ArucoDetector(stream)
    server = StreamServer(detector)
    stream.start()
    detector.start()
    server.start()
    print('SERVER READY - ENTER TO TERMINATE')
    input()
    detector.stop()
    server.stop()

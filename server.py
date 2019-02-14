from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import argparse
import cv2


class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        event = self.source.subscribe()
        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--frame')
        self.end_headers()

        while not self.server.stopped:
            event.wait(1)
            event.clear()

            if self.source.frame is None: continue
            ok, jpg = cv2.imencode('.jpg', self.source.frame)
            data = jpg.tobytes()

            self.wfile.write('--frame\r\n'.encode())
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', len(data))
            self.end_headers()
            self.wfile.write(data)


class StreamServer(Thread):
    def __init__(self, source, host='0.0.0.0', port=80):
        super().__init__()
        handler = type('Handler', (StreamHandler,), {'source': source})
        self.server = HTTPServer((host, port), handler)
        self.server.stopped = False
        self.run = self.server.serve_forever

    def stop(self):
        self.server.stopped = True
        self.server.shutdown()
        self.join()


if __name__ == '__main__':
    from camera import PiStream, CVStream, FakeStream
    from detection import ArucoDetector

    streams = {
        'pi': PiStream,
        'cv': CVStream,
        'fake': FakeStream,
        'aruco+pi': lambda **k: ArucoDetector(PiStream(**k)),
        'aruco+cv': lambda **k: ArucoDetector(CVStream(**k)),
    }

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--stream', choices=streams.keys(), default='fake')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=80)
    parser.add_argument('--width', type=int, default=720)
    parser.add_argument('--height', type=int, default=480)
    parser.add_argument('--fps', type=int, default=30)
    args = parser.parse_args()

    resolution = (args.width, args.height) if args.width and args.height else None
    stream = streams[args.stream](resolution=resolution, framerate=args.fps)
    server = StreamServer(stream, args.host, args.port)
    stream.start()
    server.start()
    print('SERVER READY - ENTER TO TERMINATE')
    input()
    stream.stop()
    server.stop()

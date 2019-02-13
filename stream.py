from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import argparse
import cv2


class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        event = self.stream.subscribe()
        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--frame')
        self.end_headers()

        while True:  # while connection_is_alive?
            event.wait()
            event.clear()

            ok, jpg = cv2.imencode('.jpg', self.stream.frame)
            if not ok: continue
            data = jpg.tobytes()

            self.wfile.write('--frame\r\n'.encode())
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', len(data))
            self.end_headers()
            self.wfile.write(data)


class StreamServer(Thread):
    def __init__(self, stream, host='0.0.0.0', port=80):
        super().__init__()
        handler = type('Handler', (StreamHandler,), {'stream': stream})
        self.server = HTTPServer((host, port), handler)
        self.run = self.server.serve_forever

    def stop(self):
        self.server.shutdown()
        self.join()


if __name__ == '__main__':
    from camera import PiStream, CVStream, FakeStream

    streams = {
        'pi': PiStream,
        'cv': CVStream,
        'fake': FakeStream
    }

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-s', '--stream', choices=streams.keys(), default='fake')
    parser.add_argument('-h', '--host', default='0.0.0.0')
    parser.add_argument('-p', '--port', type=int, default=80)
    args = parser.parse_args()

    stream = streams[args.stream]()
    server = StreamServer(stream, args.host, args.port)
    stream.start()
    server.start()
    input('READY\n')
    stream.stop()
    server.stop()

from http.server import HTTPServer, BaseHTTPRequestHandler
from multiprocessing import Process
import cv2


class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.frame = self.source.frame
        self.camconfig = self.source.config

        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--frame')
        self.end_headers()

        while not self.server.stopped:
            self.event.wait()
            self.event.clear()

            frame = self.camconfig.loadframe(frame.value)
            ok, jpg = cv2.imencode('.jpg', frame)
            data = jpg.tobytes()

            self.wfile.write('--frame\r\n'.encode())
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', len(data))
            self.end_headers()
            self.wfile.write(data)


class Server(Process):
    def __init__(self, source, event):
        super().__init__()
        handler = type('Handler', (StreamHandler,), {
            'frame': source.frame,
            'event': event
        })

        host, port = '0.0.0.0', 80  # TODO
        self.server = HTTPServer((host, port), handler)
        self.server.stopped = False
        self.run = self.server.serve_forever

    def stop(self):
        self.server.stopped = True
        self.server.shutdown()
        self.join()

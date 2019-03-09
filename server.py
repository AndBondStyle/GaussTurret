from multiprocessing import Process, Event
from aiohttp import web
import numpy as np
import sys, os
import cv2


class Server(Process):
    def __init__(self, buffer, event):
        super().__init__()
        self.buffer = buffer
        self.event = event
        self.app = web.Application()
        self.app.add_routes([
            web.get('/', self.stream)
        ])

    def run(self):
        self.frame = np.ctypeslib.as_array(self.buffer.get_obj())
        self.frame = self.frame.reshape((200, 200, 3))
        web.run_app(self.app, port=80)

    async def stream(self, request):
        response = web.StreamResponse()
        response.content_type = 'multipart/x-mixed-replace; boundary=--frame'
        response.enable_chunked_encoding()
        await response.prepare(request)

        while True:  # TODO: FIX
            self.event.wait()  # TODO: TIMEOUT?
            self.event.clear()

            _, jpeg = cv2.imencode('.jpg', self.frame)
            jpeg = jpeg.tobytes()

            data = '\r\n'.join((
                '--frame',
                'Content-type: image/jpeg',
                'Content-length: %s' % len(jpeg),
                '', ''  # It just works!
            )).encode() + jpeg

            try: await response.write(data)
            except: return  # TODO: ???

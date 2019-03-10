from threading import Thread
from aiohttp import web
import asyncio
import cv2


class Server(Thread):
    def __init__(self, core):
        super().__init__()
        self.core = core
        self.motion = core.motion
        self.event = self.core.subscribe()
        self.stopped = False
        self.loop = None
        self.runner = None
        self.app = web.Application()
        self.app.add_routes([
            web.get('/', self.index),
            web.post('/control', self.control),
            web.get('/stream', self.stream),
            web.get('/status', self.status),
        ])

    async def index(self, _):
        return web.FileResponse('index.html')

    async def control(self, request):
        data = await request.json()
        print(data)
        propchain = data['target'].split('.')
        prev, last = self, self
        for i in propchain: prev, last = last, getattr(last, i)
        if data['action'] == 'set': setattr(prev, propchain[-1], data['value'])
        elif data['action'] == 'call': last(*data.get('value', []))
        self.motion.update()
        return web.Response(text='OK')

    async def status(self, _):
        data = {
            'onborder': self.core.motion.onborder,
            'armed': self.core.motion.armed,
            'slowmode': self.core.motion.slowmode,
            'abs_rotation': self.core.motion.abs_rotation,
            'rotation': self.core.motion.rotation,
            'angle': self.core.motion.angle,
            'faces': self.core.faces,
            'markers': self.core.markers,
        }
        return web.json_response(data)

    async def stream(self, request):
        response = web.StreamResponse()
        response.content_type = 'multipart/x-mixed-replace; boundary=--frame'
        response.enable_chunked_encoding()
        await response.prepare(request)

        while not self.stopped:
            self.event.wait()
            if self.stopped: break
            self.event.clear()

            _, jpeg = cv2.imencode('.jpg', self.core.frame)
            jpeg = jpeg.tobytes()

            data = '\r\n'.join((
                '--frame',
                'Content-type: image/jpeg',
                'Content-length: %s' % len(jpeg),
                '', ''  # It just works!
            )).encode() + jpeg

            # Let asyncio handle other requests
            await asyncio.sleep(0)
            try: await response.write(data)
            except: break

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.run_coroutine_threadsafe(self.run_async(), self.loop)
        self.loop.run_forever()

    async def run_async(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '0.0.0.0', 80)
        await site.start()

    def stop(self):
        self.stopped = True
        if not self.event.is_set(): self.event.set()
        asyncio.run_coroutine_threadsafe(self.stop_async(), self.loop)
        self.join()

    async def stop_async(self):
        await self.runner.cleanup()
        self.loop.stop()

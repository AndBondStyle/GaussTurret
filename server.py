from threading import Thread
from aiohttp import web
import asyncio
import cv2


class Server(Thread):
    def __init__(self, core):
        super().__init__()
        self.core = core
        self.event = self.core.subscribe()
        self.stopped = False
        self.loop = None
        self.runner = None
        self.site = None
        self.app = web.Application()
        self.app.add_routes([
            web.get('/stream', self.stream),
            web.get('/status', self.status)
        ])

    async def status(self, _):
        data = {
            'motion': {
                'onborder': self.core.motion.onborder,
                'armed': self.core.motion.armed,
                'slowmode': self.core.motion.slowmode,
                'abs_rotation': self.core.motion.abs_rotation,
                'rotation': self.core.motion.rotation,
                'angle': self.core.motion.angle,
            },
            'core': {
                # TODO
            }
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

            try: await response.write(data)
            except: break

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
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

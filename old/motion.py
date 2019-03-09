from threading import Thread
from gpiozero import LED
from time import sleep


class Motion(Thread):
    def __init__(self):
        super().__init__()
        self.step = LED(17)
        self.dir = LED(18)
        self.speed = 100
        self.delay = 1 / self.speed
        self.steps = 0
        self.stopped = False

    def stop(self):
        self.stopped = True
        self.join()

    def run(self):
        while not self.stopped:
            sleep(self.delay)
            self.step.off()
            if not self.steps: continue
            if self.steps > 0: self.dir.on()
            else: self.dir.off()
            self.step.on()
            self.steps += 1 if self.steps < 0 else -1

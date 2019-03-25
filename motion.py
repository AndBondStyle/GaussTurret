# Raspberry Pi Zero | PyPI: gpiozero
try: from gpiozero import LED
except ImportError: pass

# Orange Pi | PyPI: OPi.GPIO
try: import OPi.GPIO as GPIO
except ImportError: pass

from threading import Thread, Event, Timer
from math import copysign
from time import sleep


class BaseMotion(Thread):
    def __init__(self, params):
        super().__init__()
        self.speed = params['SPEED']
        self.slowspeed = params['SLOWSPEED']
        self.reverse = params['REVERSE']
        self.revolution = params['REVOLUTION']
        self.rotation_range = params['ROTATION_RANGE']
        self.sleep_timeout = params['SLEEP_TIMEOUT']
        self.fire_pulse = params['FIRE_PULSE']
        self.recharge_time = params['RECHARGE_TIME']
        self.min_pwm = params['MIN_PWM']
        self.max_pwm = params['MAX_PWM']
        self.pwm_range = self.max_pwm - self.min_pwm

        self.enable_pin = lambda x: None
        self.step_pin = lambda x: None
        self.dir_pin = lambda x: None
        self.pwm_pin = lambda x: None
        self.fire_pin = lambda x: None

        self.stopped = False
        self.onborder = False
        self.armed = False
        self.slowmode = False
        self.sleep = Event()
        self.sleep.set()
        self.abs_rotation = 0
        self.rotation = 0
        self.angle = 0
        self.update = self.sleep.set

    def rotate(self, value):
        self.rotation = value
        self.update()

    def step(self, value):
        value = value or 0
        rotation = value / self.revolution
        self.rotate(rotation)

    def fire(self):
        if not self.armed: return
        self.fire_pin(True)
        sleep(self.fire_pulse)
        self.fire_pin(False)

    def stop(self):
        self.stopped = True
        self.sleep.set()
        self.join()

    def run(self):
        while not self.stopped:
            if not self.sleep.is_set():
                self.sleep.wait(self.sleep_timeout)
                if self.stopped: break
                if not self.sleep.is_set():
                    self.enable_pin(True)
                    continue

            self.enable_pin(False)
            self.step_pin(False)
            self.pwm_pin(self.min_pwm + self.angle * self.pwm_range)
            self.dir_pin((self.rotation > 0) ^ self.reverse)

            if abs(self.rotation) < 1 / self.revolution:
                self.rotation = 0
                self.sleep.clear()
                continue

            delta = copysign(1 / self.revolution, self.rotation)
            if self.rotation_range and abs(self.abs_rotation - delta) > self.rotation_range:
                self.onborder = True
                continue

            self.onborder = False
            self.rotation -= delta
            self.abs_rotation -= delta
            self.step_pin(True)
            speed = self.speed if not self.slowmode else self.slowspeed
            sleep(1 / speed)


class FakeMotion(BaseMotion):
    def __init__(self, _, params):
        super().__init__(params)
        # self.enable_pin = lambda x: print('[M] ENABLE PIN ->', 'ON' if x else 'OFF')
        self.step_pin = lambda x: x and print('[M] <<< STEP >>>')
        # self.dir_pin = lambda x: print('[M] DIR PIN ->', 'ON' if x else 'OFF')
        # self.pwm_pin = lambda x: print('[M] PWM PIN ->', x)
        self.fire_pin = lambda x: x and print('[M] <<< FIRE >>>')


class OPiMotion(BaseMotion):
    def __init__(self, pins, params):
        super().__init__(params)
        GPIO.setboard(GPIO.ZEROPLUS2H5)
        GPIO.setmode(GPIO.BOARD)

        GPIO.setup(pins['ENABLE'], GPIO.OUT)
        GPIO.setup(pins['STEP'], GPIO.OUT)
        GPIO.setup(pins['DIR'], GPIO.OUT)
        # GPIO.setup(pins['PWM'], GPIO.OUT)
        GPIO.setup(pins['FIRE'], GPIO.OUT)

        self.enable_pin = lambda x: GPIO.output(pins['ENABLE'], x)
        self.step_pin = lambda x: print('step') or GPIO.output(pins['STEP'], x)
        self.dir_pin = lambda x: GPIO.output(pins['DIR'], x)
        self.pwm_pin = lambda x: print('[M] PWM PIN ->', x)
        self.fire_pin = lambda x: GPIO.output(pins['FIRE'], x)

    def stop(self):
        super().stop()
        GPIO.cleanup()

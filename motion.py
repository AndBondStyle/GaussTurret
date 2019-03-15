# Raspberry Pi Zero | PyPI: gpiozero
try: from gpiozero import LED                           # Безопасный импорт библиотеки GPIO для старой платы:
except ImportError: pass                                # Raspberry Pi Zero

# Orange Pi | PyPI: OPi.GPIO
try: import OPi.GPIO as GPIO                            # Безопасный импорт библиотеки GPIO для текущей платы:
except ImportError: pass                                # Orange Pi Zero Plus 2 H5

from threading import Thread, Event                     # Импорт двух классов: поток и событие
from math import copysign                               # Импорт функции, копирующей знак одного числа на другое
from time import sleep                                  # Импорт функции sleep(x) - ничего не делать (спать) x секунд


class BaseMotion(Thread):            # Базовый класс, отвечающий за управление моторами. Наследуется от потока (Thread)
    def __init__(self, params):                         # Конструктор
        super().__init__()                              # Вызов конструктора родителя
        self.speed = params['SPEED']                    # Нормальная скорость (шагов в секунду)
        self.slowspeed = params['SLOWSPEED']            # Медленная скорость (шагов в секунду)
        self.reverse = params['REVERSE']                # Инвертировать направление вращения (bool)
        self.revolution = params['REVOLUTION']          # Сколько шагов шагового двигателя в полном обороте
        self.rotation_range = params['ROTATION_RANGE']  # Ограничение на модуль поворота (0.25 = от -90 до +90 градусов)
        self.sleep_timeout = params['SLEEP_TIMEOUT']    # Сколько секунд ждать прежде чем отключить моторы
        self.fire_pulse = params['FIRE_PULSE']          # Длительность импульса на выстрел (пока только для красоты)
        # self.recharge_time = params['RECHARGE_TIME']  # |
        # self.min_pwm = params['MIN_PWM']              # | Пока не используются
        # self.max_pwm = params['MAX_PWM']              # |
        # self.pwm_range = self.max_pwm - self.min_pwm  # |

        # Описание полей, которые будут переопределены в потомках класса BaseMotion (см. ниже)
        # Каждый "пин" - функция, принимающая один единственный аргумент типа bool и выставляющая соответствующий
        # логический уровень на реальном физическом "пине" (или печатающая что-то в консоль, как делает FakeMotion)
        self.enable_pin = None    # Пин включения-выключения драйвера шагового двигателя (1 = ВЫКЛ, 0 = ВКЛ)
        self.step_pin = None      # Пин "сделать шаг". Шаг происходит в момент изменения логического уровня (0 -> 1)
        self.dir_pin = None       # Пин "направление шага". 1 = в какую-то одну сторону, 0 = в противоположную
        # self.pwm_pin = None     # | Пока не используется
        self.fire_pin = None      # Пин "огонь". Сейчас просто зажигает светодиод на длительность FIRE_PULSE секунд

        self.stopped = False      # Остановлен ли поток (bool)
        self.onborder = False     # Находится ли турель на краю допустимого угла (см. ROTATION_RANGE выше)
        self.armed = False        # Разрешена ли стрельба (слово английское, буквальный перевод: "вооруженный")
        self.slowmode = False     # Включен ли "медленный режим". Просто меняет скорость на медленную (SLOWSPEED)
        self.sleep = Event()      # Событие (не путать с C#), показывающее, находится ли поток в спящем состоянии
        self.sleep.set()          # Когда УСТАНОВЛЕНО (.set()) - поток НЕ СПИТ; Когда не уст-но (.clear()) - ...
        self.abs_rotation = 0     # Абсолютное вращение. = 0 в момент запуска, в процессе программы не сбрасывается
        # self.angle = 0          # | Пока не используется

        # Относительное вращение (кол-во оборотов), меняется в процессе работы программы
        # Задача класса BaseMotion - постепенно изменяеть эту перменную, пока она не станет равна нулю, причем
        # каждое такое изменение сопровождается одним шагом мотора
        self.rotation = 0

        # Alias (псевдоним) для self.sleep.set
        # Вызов .update() равносилен команде "проснуться" (см. self.sleep выше)
        self.update = self.sleep.set

    def fire(self):                                     # "Огонь"
        if not self.armed: return                       # Если стрельба не разрешена - выход, в противном случае:
        self.fire_pin(True)                             # Подать на пин "огонь" высокий уровень (1)
        sleep(self.fire_pulse)                          # Подождать FIRE_PULSE секунд
        self.fire_pin(False)                            # Возвратить пин в низкий уровать (0)

    def stop(self):                                     # Остановть поток
        self.stopped = True                             # Остановлен ли поток = ДА
        self.update()                                   # Разбудить
        self.join()                                     # Дождаться завершения (завершения метода run)

    def run(self):                                      # Основной метод потока
        while not self.stopped:                         # Главный цикл (работает пока self.stopped = False)
            if not self.sleep.is_set():                 # Если событие НЕ установлено (т.е. поток спит)
                # Подождать пока его (событие) кто-нибудь не установит в течение SLEEP_TIMEOUT секунд
                self.sleep.wait(self.sleep_timeout)
                if self.stopped: break                  # Если поток остановили - выйти из главного цикла
                if not self.sleep.is_set():             # Если поток так и не разбудили:
                    self.enable_pin(True)               # Выключить драйвер шагового двигателя
                    continue                            # Перейти к началу главного цикла

            # Если же поток не спит:

            self.enable_pin(False)                              # Включить драйвер шагового двигателя
            self.step_pin(False)                                # Установить пин "шаг" в 0
            # Установить пин "направление" в зависимости от знака rotation XOR константы REVERSE
            self.dir_pin((self.rotation > 0) ^ self.reverse)

            if abs(self.rotation) < 1 / self.revolution:        # Если модуль вращение меньше, чем один шаг двигателя
                self.rotation = 0                               # то сбросить его в ноль
                self.sleep.clear()                              # и начать отдыхать (спать)
                continue                                        # и перейти в начало цикла

            # Сложная математика - delta показывает, как изменится rotation после шага, который вот-вот произойдет
            # 1 / revolution - это, собственно, сколько поворотов (оборотов) в одном шаге двигателя
            # Ну и на это значение копируется знак числа rotation
            delta = copysign(1 / self.revolution, self.rotation)
            # Если ограничение на вращение != 0 И модуль абсолютного вращения с учетом будущего (еще не сделанного)
            # шага больше чем ограничение на вращение:
            if self.rotation_range and abs(self.abs_rotation - delta) > self.rotation_range:
                self.onborder = True                            # "На краю" = ДА
                continue                                        # В начало цикла

            self.onborder = False                                           # "На краю" = НЕТ
            self.rotation -= delta                                          # Обновить вращение
            self.abs_rotation -= delta                                      # Обновить абсолютное вращение
            self.step_pin(True)                                             # Подать на пин "шаг" единицу
            # Выбрать нужную скорость в зависимости от режима
            # Скорость измеряется в шагах в секунду, т.е. 1 / скорость = сколько-то секунд (миллисекунд)
            speed = self.speed if not self.slowmode else self.slowspeed
            sleep(1 / speed)                                                # Подождать "сколько-то миллисекунд"


class FakeMotion(BaseMotion):                # Фейковый класс (для тестирования программы без электроники)
    def __init__(self, _, params):
        super().__init__(params)
        # Вместо того чтобы управлять пинами просто печатает что с ними происходит в консоль
        # Как работают лямбды думаю понятно
        self.enable_pin = lambda x: print('[M] ENABLE PIN ->', 'ON' if x else 'OFF')
        self.step_pin = lambda x: print('[M] STEP PIN ->', 'ON' if x else 'OFF')
        self.dir_pin = lambda x: print('[M] DIR PIN ->', 'ON' if x else 'OFF')
        self.pwm_pin = lambda x: print('[M] PWM PIN ->', x)
        self.fire_pin = lambda x: print('[M] FIRE PIN ->', 'ON' if x else 'OFF')


class OPiMotion(BaseMotion):                  # Настоящий класс. Агрументы конструктора: словарь с номерами пинов и
    def __init__(self, pins, params):         # словарь с параметрами движения (см. файл main.py)
        super().__init__(params)              # Вызов констуктора родителя, куда передаются параметры движения
        # Далее все, что начинается с "GPIO" - фукнции специальной библиотеки, которая управляет пинами
        GPIO.setboard(GPIO.ZEROPLUS2H5)       # Выбор модели платы: Zero Plus 2 H5
        GPIO.setmode(GPIO.BOARD)              # Выбор режима нумерации пинов: обычный (1, 2, 3 ...)

        # Инициализация пинов. GPIO.OUT значит что пин инициализируется как ВЫХОД
        # Соответственно GPIO.IN это "инициализировать как ВХОД", но тут такого нет
        GPIO.setup(pins['ENABLE'], GPIO.OUT)  # |
        GPIO.setup(pins['STEP'], GPIO.OUT)    # | Все те же пины что и в BaseMotion, повторять что они значат смысла нет
        GPIO.setup(pins['DIR'], GPIO.OUT)     # |
        GPIO.setup(pins['FIRE'], GPIO.OUT)    # |
        # GPIO.setup(pins['PWM'], GPIO.OUT)   # | Этот пока не используется

        # Инициализация функций, которые будет вызывать BaseMotion (см. выше, что они должны принимать)
        # GPIO.output - библиотечная функция, которая выдает на пин высокий или низкий уровень (1 или 0)
        self.enable_pin = lambda x: GPIO.output(pins['ENABLE'], x)
        self.step_pin = lambda x: GPIO.output(pins['STEP'], x)
        self.dir_pin = lambda x: GPIO.output(pins['DIR'], x)
        self.fire_pin = lambda x: GPIO.output(pins['FIRE'], x)
        # self.pwm_pin = lambda x: print('[M] PWM PIN ->', x)  # Пока не используется

    def stop(self):      # Остановка потока (переопределенный метод)
        super().stop()   # Сначала вызываем соответствующий метод родителя
        GPIO.cleanup()   # А потом специальную библиотечную функцию, освобождающую пины из рабского плена

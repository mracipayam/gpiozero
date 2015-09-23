from time import sleep
from threading import Lock

from RPi import GPIO

from .devices import GPIODeviceError, GPIODevice, GPIOThread


class OutputDeviceError(GPIODeviceError):
    pass


class OutputDevice(GPIODevice):
    def __init__(self, pin=None):
        super(OutputDevice, self).__init__(pin)
        GPIO.setup(pin, GPIO.OUT)

    def on(self):
        GPIO.output(self.pin, True)

    def off(self):
        GPIO.output(self.pin, False)


class DigitalOutputDevice(OutputDevice):
    def __init__(self, pin=None):
        super(DigitalOutputDevice, self).__init__(pin)
        self._blink_thread = None
        self._lock = Lock()

    def on(self):
        self._stop_blink()
        super(DigitalOutputDevice, self).on()

    def off(self):
        self._stop_blink()
        super(DigitalOutputDevice, self).off()

    def blink(self, on_time=1, off_time=1):
        self._stop_blink()
        self._blink_thread = GPIOThread(
            target=self._blink_led, args=(on_time, off_time)
        )
        self._blink_thread.start()

    def _stop_blink(self):
        if self._blink_thread:
            self._blink_thread.stop()
            self._blink_thread = None

    def _blink_led(self, on_time, off_time):
        while True:
            super(DigitalOutputDevice, self).on()
            if self._blink_thread.stopping.wait(on_time):
                break
            super(DigitalOutputDevice, self).off()
            if self._blink_thread.stopping.wait(off_time):
                break

    def toggle(self):
        with self._lock:
            if self.is_active:
                self.off()
            else:
                self.on()


class LED(DigitalOutputDevice):
    pass


class Buzzer(DigitalOutputDevice):
    pass


class Motor(OutputDevice):
    pass


class Robot(object):
    def __init__(self, left=None, right=None):
        if not all([left, right]):
            raise GPIODeviceError('left and right pins must be provided')

        self._left = Motor(left)
        self._right = Motor(right)

    def left(self, seconds=None):
        self._left.on()
        if seconds is not None:
            sleep(seconds)
            self._left.off()

    def right(self, seconds=None):
        self._right.on()
        if seconds is not None:
            sleep(seconds)
            self._right.off()

    def forwards(self, seconds=None):
        self.left()
        self.right()
        if seconds is not None:
            sleep(seconds)
            self.stop()

    def stop(self):
        self._left.off()
        self._right.off()

from pyControl.hardware import Digital_output


class Stepper_motor:
    def __init__(self, port=None, direction_pin=None, step_pin=None):
        if port:
            direction_pin = port.DIO_A
            step_pin = port.DIO_B
        self._direction = Digital_output(direction_pin)
        self._step = Digital_output(step_pin)

    def forward(self, step_rate, n_steps=False):
        self._direction.off()  # set direction forward
        self._step.pulse(step_rate, n_pulses=n_steps)

    def backward(self, step_rate, n_steps=False):
        self._direction.on()  # set direction back
        self._step.pulse(step_rate, n_pulses=n_steps)

    def stop(self):
        self._step.off()

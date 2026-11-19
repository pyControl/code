import pyb
import pyControl.hardware as hw
from pyControl.hardware import Analog_input

# CPU pins wired to each encoder-capable timer's CH1 and CH2 inputs, on the STM32F405
# (pyboard) and STM32H743. Only CH1 and CH2 feed a timer's quadrature encoder; a pin on
# another channel of the same timer would be accepted by the MCU but never count. Not
# exhaustive for every package: a pin missing here is rejected, never silently miswired.
ENCODER_CHANNEL_PINS = {
    1: (("A8", "E9"), ("A9", "E11")),
    2: (("A0", "A5", "A15"), ("A1", "B3")),
    3: (("A6", "B4", "C6"), ("A7", "B5", "C7")),
    4: (("B6", "D12"), ("B7", "D13")),
    5: (("A0", "H10"), ("A1", "H11")),
    8: (("C6", "I5"), ("C7", "I6")),
}


def _encoder_channel(pin_name, timer):
    # Return 1 or 2 if the CPU pin is the timer's CH1 or CH2 input, otherwise None.
    ch1_pins, ch2_pins = ENCODER_CHANNEL_PINS[timer]
    if pin_name in ch1_pins:
        return 1
    if pin_name in ch2_pins:
        return 2
    return None


def _timer_alternate_function(pin, timer):
    # Return the alternate function index connecting pin to timer, read from the MCU's pin table.
    suffix = "_TIM{}".format(timer)
    for af in pin.af_list():
        if af.name().endswith(suffix):
            return af.index()
    raise ValueError("Pin {} is not connected to timer {}.".format(pin.name(), timer))


class Rotary_encoder(Analog_input):
    # Quadrature output rotary encoder.
    #
    # Select the input with either:
    #   port=board.port_N           A breakout port whose Port() sets ENCODER.
    #   pin_a=, pin_b=, timer=      One pin on that timer's CH1 and one on its CH2
    #                               (see ENCODER_CHANNEL_PINS).
    # With neither, the upstream default is used: pins X1/X2 on timer 2 (port 1 of
    # breakout v1.x). Swapping pin_a and pin_b reverses direction, like reverse=True.
    def __init__(
        self,
        name,
        sampling_rate,
        output="velocity",
        threshold=None,
        rising_event=None,
        falling_event=None,
        bytes_per_sample=2,
        reverse=False,
        triggers=None,
        port=None,
        pin_a=None,
        pin_b=None,
        timer=None,
    ):
        assert output in ("velocity", "position"), "ouput argument must be 'velocity' or 'position'."
        assert bytes_per_sample in (2, 4), "bytes_per_sample must be 2 or 4"
        self.output_velocity = output == "velocity"
        self.reverse = reverse
        explicit = (pin_a, pin_b, timer)
        if port is not None:
            if explicit != (None, None, None):
                raise ValueError("Rotary_encoder: specify either port or pin_a/pin_b/timer, not both.")
            if getattr(port, "ENCODER", None) is None:
                raise ValueError("Rotary_encoder: this port does not support an encoder (its Port() has no ENCODER).")
            pin_a, pin_b, timer = port.DIO_A, port.DIO_B, port.ENCODER
        elif explicit == (None, None, None):
            pin_a, pin_b, timer = "X1", "X2", 2
        elif None in explicit:
            raise ValueError("Rotary_encoder: pin_a, pin_b and timer must be specified together.")
        if timer not in ENCODER_CHANNEL_PINS:
            raise ValueError(
                "Rotary_encoder: timer {} has no encoder mode; use one of {}.".format(
                    timer, tuple(sorted(ENCODER_CHANNEL_PINS))
                )
            )
        try:
            pin_a, pin_b = pyb.Pin(pin_a), pyb.Pin(pin_b)
        except ValueError as e:
            if port is None and explicit == (None, None, None):
                raise ValueError("Rotary_encoder: this board has no X1/X2 pins; pass port=board.port_N.")
            raise ValueError("Rotary_encoder: {}".format(e))
        channels = (
            _encoder_channel(pin_a.name(), timer),
            _encoder_channel(pin_b.name(), timer),
        )
        if set(channels) != {1, 2}:
            ch1_pins, ch2_pins = ENCODER_CHANNEL_PINS[timer]
            raise ValueError(
                "Rotary_encoder: pins {} and {} are not timer {}'s CH1 and CH2 inputs (CH1: {}, CH2: {}).".format(
                    pin_a.name(),
                    pin_b.name(),
                    timer,
                    ", ".join(ch1_pins),
                    ", ".join(ch2_pins),
                )
            )
        try:
            af_a = _timer_alternate_function(pin_a, timer)
            af_b = _timer_alternate_function(pin_b, timer)
        except ValueError as e:
            raise ValueError("Rotary_encoder: {}".format(e))
        hw.claim_timer(timer, "Rotary_encoder '{}'".format(name))
        self.pin_a = pyb.Pin(pin_a, pyb.Pin.AF_PP, pull=pyb.Pin.PULL_NONE, af=af_a)
        self.pin_b = pyb.Pin(pin_b, pyb.Pin.AF_PP, pull=pyb.Pin.PULL_NONE, af=af_b)
        self.counter_modulus = 0x10000
        self.counter_half_modulus = self.counter_modulus // 2
        self.enc_timer = pyb.Timer(timer, prescaler=1, period=self.counter_modulus - 1)
        self.enc_channel = self.enc_timer.channel(1, pyb.Timer.ENC_AB)
        self.position = 0
        self.velocity = 0
        self.sampling_rate = sampling_rate

        Analog_input.__init__(
            self,
            None,
            name,
            int(sampling_rate),
            threshold,
            rising_event,
            falling_event,
            data_type={2: "h", 4: "i"}[bytes_per_sample],
            triggers=triggers,
        )

    def read_sample(self):
        # Read value of encoder counter, correct for rollover, return position or velocity.
        new_counter_value = self.enc_timer.counter()
        counter_change = new_counter_value - self.counter_value
        self.counter_value = new_counter_value
        if counter_change > self.counter_half_modulus:  # Backward counter rollover.
            counter_change -= self.counter_modulus
        elif counter_change < -self.counter_half_modulus:  # Forward counter rollover.
            counter_change += self.counter_modulus
        if self.reverse:
            counter_change = -counter_change
        self.position += counter_change
        self.velocity = counter_change * self.sampling_rate
        if self.output_velocity:
            return self.velocity
        else:
            return self.position

    def _run_start(self):
        # Start sampling analog input values.
        self.counter_value = self.enc_timer.counter()
        Analog_input._run_start(self)

import pyb
from pyControl.hardware import Analog_input


class Rotary_encoder(Analog_input):
    # Quadrature output rotary encoder.
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
    ):
        assert output in ("velocity", "position"), "ouput argument must be 'velocity' or 'position'."
        assert bytes_per_sample in (2, 4), "bytes_per_sample must be 2 or 4"
        self.output_velocity = output == "velocity"
        self.reverse = reverse
        self.pin_a = pyb.Pin("X1", pyb.Pin.AF_PP, pull=pyb.Pin.PULL_NONE, af=pyb.Pin.AF1_TIM2)
        self.pin_b = pyb.Pin("X2", pyb.Pin.AF_PP, pull=pyb.Pin.PULL_NONE, af=pyb.Pin.AF1_TIM2)
        self.counter_max_value = 0xFFFF
        self.counter_half_max_value = self.counter_max_value // 2
        self.enc_timer = pyb.Timer(2, prescaler=1, period=self.counter_max_value)
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
        )

    def read_sample(self):
        # Read value of encoder counter, correct for rollover, return position or velocity.
        new_counter_value = self.enc_timer.counter()
        counter_change = new_counter_value - self.counter_value
        self.counter_value = new_counter_value
        if counter_change > self.counter_half_max_value:  # Backward counter rollover.
            counter_change = counter_change - self.counter_max_value
        elif counter_change < -self.counter_half_max_value:  # Forward counter rollover.
            counter_change = counter_change & self.counter_max_value
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

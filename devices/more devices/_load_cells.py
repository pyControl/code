import pyControl.hardware as _h

class LoadCell():
    def __init__(self, port1, port2, rising_event_A = None, falling_event_A = None, rising_event_B = None, falling_event_B = None, debounce = 5):        
        self._cell_threshold_high = _h.Digital_input(port1, rising_event_A, falling_event_A, debounce)
        self._cell_threshold_low = _h.Digital_input(port2, rising_event_B, falling_event_B, debounce)

    @property
    def high_rising(self):
        return self._cell_threshold_high.rising_event

    @property
    def high_falling(self):
        return self._cell_threshold_high.falling_event
    @property
    def low_rising(self):
        return self._cell_threshold_low.rising_event
    @property
    def low_falling(self):
        return self._cell_threshold_low.falling_event


class LoadCellsTriggers():
    def __init__(self, task_port, solenoid_port, infrared_port):

        self.task_status = _h.Digital_output(task_port)
        self.solenoid_status = _h.Digital_output(solenoid_port)
        self.infrared_status = _h.Digital_output(infrared_port)

    def start_task(self):
        self.task_status.on()

    def stop_task(self):
        self.task_status.off()

    def solenoid_opening(self):
        self.solenoid_status.on()

    def solenoid_closing(self):
        self.solenoid_status.off()        
    
    def infrared_cross_in(self):
        self.infrared_status.on()     

    def infrared_cross_out(self):
        self.infrared_status.off()  	


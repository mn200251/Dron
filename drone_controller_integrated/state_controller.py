import numpy as np

class StateController():
    def __init__(self):
        self.pid_sleep_time = 10
        self.sensor_measure_interval = 7
        self.pid_reset_interval_factor = 1
        self.loop_cycle = 1
        self.pid_activation_cycle = 0
        self.lcm = np.lcm(self.pid_sleep_time, self.sensor_measure_interval)
    
    def load_params_from_file(self, file):
        # to do
        pass
        lcm = np.lcm(self.pid_sleep_time, self.sensor_measure_interval)
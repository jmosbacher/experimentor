from typing import Iterable, Dict
from .measurements import Measurement
from .protocol import Protocol


class Experiment:

    def __init__(self, system, working_dir: str, protocol: Protocol,
                 measurements: Iterable[Measurement]):
        self.system = system
        self.wd = working_dir
        self.protocol = protocol
        self.measurements = measurements

    def run(self):
        for idx, state, new_state in self.protocol:
            self.system.set_state(new_state)
            for measurement in self.measurements:
                measurement.perform(idx, self.system, state)


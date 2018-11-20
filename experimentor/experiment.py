from typing import Iterable, Dict
from .measurements import Measurement
from .protocol import Protocol
import logging
import os
import time

logger = logging.getLogger(__name__)


class Experiment:
    attributes = []

    def __init__(self, name, system, working_dir: str, protocol: Protocol,
                 measurements: Iterable[Measurement], metadata={},
                 validate_state=False):
        self.name = name
        self.system = system
        self.system.experiment = self
        self.wd = working_dir
        self.protocol = protocol
        self.measurements = measurements
        self.validate_state = validate_state

    def run(self):
        self.log_experiment()
        for idx, state, new_state in self.protocol:
            self.system.set_state(new_state)
            if self.validate_state:
                state = self.system.get_state()
            logger.log(str(state))
            for measurement in self.measurements:
                measurement.perform(idx, self.system, state)

    def log_experiment(self):
        fname = '_'.join(self.name, "log", time.strftime("%Y%m%d_%H%M%S"))
        folder = os.path.join(self.wd, self.name)

        try:
            os.mkdir(folder)
        except FileExistsError:
            pass

        path = os.path.join(folder,fname)
        with open(path, 'w') as f:
            f.write(f"{datetime.datetime.utcnow()}:   {self.name} started.\nMetadata:\n")
            for k,v in self.metadata.items():
                f.write(f"{k} : {v}\n")
        fh = logging.FileHandler(path)
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)



from itertools import product
import time
from typing import Iterable, Dict
import json
from collections import defaultdict


class Measurement:
    name = 'measurement'

    def __init__(self, sys_state: dict):
        self.system_state = sys_state

    def perform(self, idx, system, state):
        raise NotImplementedError


class MeasurementSet(Measurement):

    def __init__(self, sys_state: dict, measurements: Iterable[Measurement]):
        super().__init__(sys_state)
        self.measurements = measurements

    def perform(self, idx, system, state):
        for meas in self.measurements:
            meas.perform(system)
            time.sleep(0.5)


class AndorSignal(Measurement):
    #name = 'Andor'

    def perform(self, idx, system, state):
        andor = system.andor
        andor.shutter = 'open'
        andor.running = True
        while andor.running:
            time.sleep(0.5)
        andor.saved = True


class AndorBackground(Measurement):
    #name = 'Andor'

    def perform(self, idx, system, state):
        andor = system.andor
        andor.shutter = 'closed'
        andor.running = True
        while andor.running:
            time.sleep(0.5)
        andor.saved = True


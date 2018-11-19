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


class SpectroSignal(Measurement):
    #name = 'Andor'

    def perform(self, idx, system, state):
        spectro = system.spectro
        spectro.shutter = 'open'
        spectro.running = True
        while spectro.running:
            time.sleep(0.5)
        spectro.saved = True


class SpectroBackground(Measurement):
    #name = 'Andor'

    def perform(self, idx, system, state):
        spectro = system.spectro
        spectro.shutter = 'closed'
        spectro.running = True
        while spectro.running:
            time.sleep(0.5)
        spectro.saved = True


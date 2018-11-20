from itertools import product
import time
from typing import Iterable, Dict
import json
from collections import defaultdict
import pymongo
import logging
import ast
import datetime
import numpy as np

logger = logging.getLogger(__name__)


class Measurement:
    name = 'measurement'

    def __init__(self, name, mongodb=None):
        self.name = name

        if mongodb is not None:
            client = pymongo.MongoClient()
            self.db = client[mongodb]
        self.db = None

    def perform(self, idx, system, state):
        raise NotImplementedError


class SpectroMeasurement(Measurement):
    @staticmethod
    def read_ascii_file(path, delim=' '):

        data = []
        metadata = {}
        with open(path, 'r') as f:
            sig = True
            for line in f:
                if line in ['\n', '\r\n']:
                    continue
                if ':' in line:
                    k, v = [x.strip() for x in line.split(':', 1)]
                    try:
                        val = ast.literal_eval(v)
                    except:
                        val = v
                    metadata[k] = val
                else:
                    d = tuple([ast.literal_eval(v) for v in line.split(delim)])
                    if d:
                        data.append(d)
        data = tuple(data)
        if data:
            return data, metadata
        else:
            return None, None

    def perform(self, idx, system, state):
        spectro = system.spectro
        system.power_meter.count = 100
        pwr = [system.power_meter.power]
        spectro.running = True
        pwr.append(system.power_meter.power)

        while spectro.running:
            pwr.append(system.power_meter.power)
            time.sleep(0.1)
        power = {
            "mean":np.mean(pwr),
            "median": np.median(pwr),
            "std": np.std(pwr),
            "samples": len(pwr),
            "counts_per_sample": 100,
        }

        spectro.saved = True
        fpath = state["spectro"]["save_path"]
        parts = fpath.split('.')
        ppath = ''.join(parts[:-1]+ ["_power."] + parts[-1])
        with open(ppath, "w") as f:
            for k,v in power.items():
                f.write(f"{k} : {v}\n")
        if self.db is not None:
            d, m = self.read_ascii_file(fpath)
            doc = {
                "creation_date": datetime.datetime.utcnow(),
                "data": d,
                "power": power,
                "metadata": m,
                "data_hash": hash(d),
                "measurement_name": self.name,
            }
            self.db[self.name].insert_one(doc)


class SpectroSignal(SpectroMeasurement):
    #name = 'Andor'

    def perform(self, idx, system, state):
        system.spectro.shutter = 'open'
        super().perform(idx, system, state)


class SpectroBackground(SpectroMeasurement):

    def perform(self, idx, system, state):
        system.spectro.shutter = 'closed'
        super().perform(idx, system, state)


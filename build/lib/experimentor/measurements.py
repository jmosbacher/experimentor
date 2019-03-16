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
import os
logger = logging.getLogger(__name__)

class Measurement:
    name = 'measurement'

    def __init__(self, name, mongodb=None):
        self.name = name

        if mongodb is not None:
            client = pymongo.MongoClient()
            self.db = client[mongodb]
        else:
            self.db = None

    def perform(self, idx, system, state):
        raise NotImplementedError


class SpectroMeasurement(Measurement):
    @staticmethod
    def read_ascii_file(path, delim='\t'):

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
        
        system.power_meter.count = 100
        system.power_meter.wavelength = state["mono"]["wavelength"]
        
        fname = state["spectro"].get("save_path", 'counts.asc')
        ext = fname.split('.')[-1]
        fpath = os.path.join(system.experiment.wd, system.experiment.name, fname.replace(f".{ext}", f"_{self.name}.{ext}" ))
        ppath = os.path.join(system.experiment.wd, system.experiment.name, fname.replace(f".{ext}", f"_{self.name}_details.{ext}" ))
        system.spectro.save_path = fpath

        pwr = [system.power_meter.power]
        system.spectro.running = True
        time.sleep(0.05)
        pwr.append(system.power_meter.power)

        while system.spectro.running:
            pwr.append(system.power_meter.power)
            time.sleep(0.05)

        power = {
            "mean":np.mean(pwr),
            "median": np.median(pwr),
            "std": np.std(pwr),
            "samples": len(pwr),
            "counts_per_sample": 100,
        }

        
        for _ in range(10):
            system.spectro.saved = True
            if os.path.isfile(fpath):
                break
            time.sleep(1)
            if os.path.isfile(fpath):
                break

        with open(ppath, "w") as f:
            for k,v in power.items():
                f.write(f"power_{k} : {v}\n")
            f.write("\n\n")
            for name, dev in state.items():
                for k,v in dev.items():
                    f.write(f"{name}_{k} : {v}\n")
                f.write("\n\n")
        
        if self.db is not None:
            d, m = self.read_ascii_file(fpath)
            doc = {
                "creation_date": datetime.datetime.utcnow(),
                "document_type": "measurement",
                "data": d,
                "power": power,
                "metadata": m,
                "data_hash": hash(d),
                "measurement_name": self.name,
                "measurement_class": self.__class__.__name__,
                "system_state": state,
                "data_file_path": fpath,
            }
            self.db[system.experiment.name].insert_one(doc)


class SpectroSignal(SpectroMeasurement):
    #name = 'Andor'
    
    def perform(self, idx, system, state):
        system.spectro.shutter = 'auto'
        system.source_shutter.on = True
        super().perform(idx, system, state)
        system.spectro.shutter = 'closed'
        system.source_shutter.on = False

class SpectroBackground(SpectroMeasurement):
    def __init__(self, name, mongodb=None):
        super().__init__( name, mongodb)
        self.last_crystal = None
        self.exposures_done = []

    def perform(self, idx, system, state):
        exp = state["spectro"].get("exposure", None)
        pos = state["crystal_wheel"].get("position", None )
        if (pos == self.last_crystal) and (exp in self.exposures_done):
            self.exposures_done = []
            return
        else:
            self.exposures_done.append(exp)
        self.last_crystal = pos
        system.spectro.shutter = 'closed'
        system.source_shutter.on = True
        super().perform(idx, system, state)
        system.source_shutter.on = False

class SpectroAmbient(SpectroMeasurement):

    def perform(self, idx, system, state):
        if state["crystal_wheel"].get("position", 0)!=0 or state["spectro"].get("exposure", 1)!=10:
            return
        system.spectro.shutter = 'auto'
        system.source_shutter.on = False
        super().perform(idx, system, state)

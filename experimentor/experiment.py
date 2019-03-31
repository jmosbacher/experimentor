from typing import Iterable, Dict
from .turtles import Turtle
import logging
import os
import time
import datetime
import configparser


def print_state_to_stdout(state):
    for dev, d in state.items():
        print(f"{dev}:")
        print(' ; '.join([f"{k}={v}" for k,v in d.items()] ))

class Experiment:

    def __init__(self, name, system,  protocol, procedures, mongodb=None, ):

        self.name = name
        self.system = system
        self.protocol = protocol
        self.procedures = procedures

        if mongodb is not None:
            import pymongo
            client = pymongo.MongoClient()
            self.db = client[mongodb]
        else:
            self.db = None

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def run(self, context={}, **settings):
        # settings = context.get("run_settings", {})
        startfrom = settings.get("startfrom" ,0) 
        skip_idxs = settings.get("skip_idxs" ,() )
        print_datetime = settings.get("print_datetime" , False)
        print_state = settings.get("print_state" ,False)
        print_state_idx = settings.get("print_state_idx" ,False)
        do_startup_checks = settings.get("do_startup_checks" ,True)
        get_initial_state = settings.get("get_initial_state" ,True)
        validate_state = settings.get("validate_state", False)
        self.wd = settings.get("working_directory", os.getcwd())

        self.setup_logging()
        if do_startup_checks:
            self.startup_checks()

        if get_initial_state:
            state = self.system.get_state_async()
            self.logger.info("Initial State:")
            self.logger.info(str(state))

        idx = 0
        # turtle = Turtle.from_protocol_file(self.protocol_file)
        for context, state in self.protocol.states(context):
            idx = context.get("count", idx+1)
            if print_datetime:
                print('-'*60)
                print(datetime.datetime.utcnow())

            if print_state_idx:
                print(idx)
                
            if idx < startfrom or (idx in skip_idxs):
                print_state_to_stdout(state)
                print(f"skipping state {idx}.")
                continue

            if print_state:
                print_state_to_stdout(state)

            self.system.set_state_async(state)
            if validate_state:
                rstate = self.system.get_state_async()
                assert all([all([rstate[d][a] == state[d][a] for a in state[d]]) for d in state])
            
            self.procedures.perform(self.system, context)

            self.logger.info(f"Finished moving to state {idx}. State changes:")
            self.logger.info(str(state))
            
 
        self.close_logs()

    def startup_checks(self):
        self.logger.info("Checking that all devices are connected.")
        for dev in self.system.devices:
            if getattr(self.system, dev).connected:
                self.logger.info(f"{dev} is connected.")
            else:
                self.logger.info(f"{dev} is NOT connected. quitting.")
                raise RuntimeError(f"{dev} is NOT connected.")

    def setup_logging(self):
        fname = '_'.join([self.name, time.strftime("%Y%m%d_%H%M%S")])+".log"
        folder = os.path.join(self.wd, self.name)

        try:
            os.mkdir(folder)
        except FileExistsError:
            pass

        path = os.path.join(folder,fname)
        # with open(path, 'w') as f:
        #     f.write(f"{datetime.datetime.utcnow()}:   {self.name} started.\n Context:\n\n")
            # for k,v in self.context.items():
            #     f.write(f"{k} : {v}\n")
            # proto_lines = []
            # with open(self.protocol_file, "r") as pf:
            #     f.write('='*25 + "  Protocol  " + '='*25 +'\n\n')
            #     for line in pf:
            #         f.write(line)
            #         proto_lines.append(line)
            #     f.write('\n\n'+'='*60+'\n\n')

        # if self.db is not None:
        #     config = configparser.ConfigParser(delimiters=(':'))
        #     config.read(self.protocol_file)
        #     proto = {name: dict(config[name]) for name in config.sections()}
        #     doc = {
        #         "creation_date": datetime.datetime.utcnow(),
        #         "document_type": "experiment",
        #         "context": self.context,
        #         "experiment_name": self.name,
        #         # "experiment_class": self.__class__.__name__,
        #         "protocol_file_path": self.protocol_file,
        #         "protocol": "\n".join(proto_lines),
        #     }
        #     self.db[self.name].insert_one(doc)

        
        fh = logging.FileHandler(path)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        fh.setLevel(logging.INFO)
        self.logger.addHandler(fh)

    def close_logs(self):
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)


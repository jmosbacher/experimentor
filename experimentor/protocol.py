from itertools import product
from collections import defaultdict
import time

class Protocol:
    def __init__(self, config: dict):
        self.config = config

    @classmethod
    def from_config_file(cls, path):
        import configparser
        config = configparser.ConfigParser()
        config.read(path)
        configs = defaultdict(list)

        for name in config.sections():
            params = dict(config[name])
            name = tuple(name.split('.'))
            t = params.pop('type', 'constant')

            params['values'] = eval(params.pop('values', '[]'))
            configs[t].append((name, params))
        cfg = cls.flatten_configs(configs)
        return cls(cfg)

    @staticmethod
    def flatten_configs(configs):
        lists = []
        for (dev, attr), cfg in configs['list']:
            alias = cfg.get("alias", f"{dev}_{attr}")
            l = [(dev, attr, alias, val) for val in cfg['values']]
            lists.append(l)

        mappings = []
        for (dev, attr), cfg in configs['mapping']:
            mapping = {val: cfg[f"{val}"] for val in cfg["values"]}
            alias = cfg.get("alias", f"{dev}_{attr}")
            mappings.append((dev, attr, alias, mapping))

        constants = []
        for (dev,), cfg in configs['constant']:
            cs = [(dev, attr, f"{dev}_{attr}", cfg[f"{attr}"]) for attr in cfg["values"]]
            constants.extend(cs)

        derivations = []
        for (dev,), cfg in configs['derivation']:
            cs = [(dev, attr, f"{dev}_{attr}", cfg[f"{attr}"]) for attr in cfg["values"]]
            derivations.extend(cs)
        
        skips = []
        for (name,), cfg in configs['skip']:
            cs = [cfg[f"{attr}"] for attr in cfg["values"]]
            skips.append((name, cs))

        config = {"lists": lists, "mappings": mappings, "skips": skips,
                  "constants": constants, "derivations": derivations}
        return config

    def __iter__(self):
        state = defaultdict(dict)
        
        local = {"timestamp": int(time.time())}

        for dev, attr, alias, val in self.config["constants"]:
            state[dev][attr] = val
            local[alias] = val

        for idx, lparams in enumerate(product(*self.config["lists"])):
            new_state = defaultdict(dict)
            local['state_idx'] = idx
            for (dev, attr, alias, val) in lparams:
                local[alias] = val
                if state[dev].get(attr, None) != val:
                    new_state[dev][attr] = val
                state[dev][attr] = val

            for dev, attr, alias, mapping in self.config['mappings']:
                for val, condition in mapping.items():
                    if eval(condition.format(**local)):
                        if state[dev].get(attr, None) != val:
                            new_state[dev][attr] = val
                        state[dev][attr] = val
                        break

            for dev, attr, alias, expression in self.config['derivations']:
                val = expression.format(**local)
                if state[dev].get(attr, None) != val:
                    new_state[dev][attr] = val
                state[dev][attr] = val

            skip = False
            for name, expressions in self.config["skips"]:
                if all([eval(exp.format(**local)) for exp in expressions]):
                    skip = True
                    break
            # state.update(new_state)
            yield idx, skip,  state, new_state

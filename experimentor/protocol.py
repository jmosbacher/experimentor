from itertools import product
from collections import defaultdict
import time

class Protocol:
    def __init__(self, iterators, maps, evaluated, excluded):
        self.iterators = iterators
        self.maps = maps
        self.evaluated = evaluated
        self.excluded = excluded

    @classmethod
    def from_config_file(cls, path):
        import configparser
        config = configparser.ConfigParser()
        config.read(path)

        aliases = dict(config['aliases'])

        iterators = []
        for name, expr in config['iterators'].items():
            dev, attr = name.split('.')
            alias = aliases.get(name, name)
            it = [(dev, attr, alias, val) for val in eval(expr)]
            iterators.append(it)

        maps = []
        for name, expr in config['mappings'].items():
            dev, attr = name.split('.')
            alias = aliases.get(name, name)
            map = dict(config[name])
            maps.append((dev, attr, alias, map))

        evaluated = []
        for name, expr in config['evaluated'].items():
            dev, attr = name.split('.')
            alias = aliases.get(name, name)
            evaluated.append((dev, attr, alias, expr))

        excluded = []
        for name, expr in config['excluded'].items():
            dev, attr = name.split('.')
            alias = aliases.get(name, name)
            excluded.append((dev, attr, alias, expr))

        return cls(iterators, maps, evaluated, excluded)


    def states(self):
        return [s for s in self.iter_states()]

    def iter_states(self):
        shared = {'state_idx':0, 'datetime': time.time()}

        # Iterate over the external product of iterators
        for iparams in product(*self.iterators):

            state = defaultdict(dict)
            for dev, attr, alias, val in iparams:
                shared[alias] = val
                state[dev][attr] = val

            # set the mapped parameters
            for dev, attr, alias, mapping in self.maps:
                for val, expr in mapping.items():
                    if eval(expr.format(**shared)):
                        shared[alias] = val
                        state[dev][attr] = val
                        break

            for dev, attr, alias, expr in self.evaluated:
                val = eval(expr.format(**shared))
                shared[alias] = val
                state[dev][attr] = val

            if any([eval(expr.format(**shared)) for expr in self.excluded]):
                continue
            shared['state_idx'] += 1
            yield state

    def __iter__(self):
        return self.iter_states()

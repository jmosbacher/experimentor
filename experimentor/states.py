from itertools import product
from collections import defaultdict
import time
from .iterators import Map, Eval, IterExpression


def lazy_product(iters):
    if not iters:
        yield ()
    else:
        for it in iters[0]:
            for rest in lazy_product(iters[1:]):
                yield (it,) + rest

class States:
    def __init__(self, iterators, excluded=()):
        self.iterators = iterators
        self.shared_state = {}

    @classmethod
    def from_config_file(cls, path):
        import configparser
        config = configparser.ConfigParser(delimiters=(':'))
        config.read(path)

        aliases = dict(config['aliases'])

        iterators = []
        for name, expr in config['iterators'].items():
            dev, attr = name.split('.')
            alias = aliases.get(name, name)
            it = IterExpression(dev, attr, alias, expr)
            iterators.append(it)


        for name, nmax in config['maps'].items():
            dev, attr = name.split('.')
            alias = aliases.get(name, name)
            map = dict(config[name])
            m = Map(dev, attr, alias, map)
            iterators.append(map)


        evaluated = []
        for name, expr in config['evaluated'].items():
            dev, attr = name.split('.')
            alias = aliases.get(name, name)

            evaluated.append((dev, attr, alias, expr))

        excluded = []
        for name, expr in config['excluded'].items():
            excluded.append((name, expr))

        return cls(iterators, tuple(excluded))


    def __iter__(self):
        self.shared_state['state_idx'] = 0
        self.shared_state['timestamp'] = int(time.time())

        for params in lazy_product(self.iterators):
            state = defaultdict(dict)
            for dev, attr, val in params:
                state[dev][attr] = val

            for name, expr in self.excluded:
                if eval(expr.format(**self.shared_state)):
                    #self.logger.info(f"skipping state due to {name}")
                    break
            else:
                self.shared_state['state_idx'] += 1
                yield state

            self.shared_state['timestamp'] = int(time.time())



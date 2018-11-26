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
    def __init__(self, iterators, shared, excluded=()):
        self.iterators = iterators
        self.shared_state = shared
        self.excluded = excluded

    @classmethod
    def from_config_file(cls, path):
        import configparser
        config = configparser.ConfigParser(delimiters=(':'))
        config.read(path)
        special = ('excluded')
        iterators = []

        shared = {}
        names = [n for n in config.sections() if n not in special]

        excluded = [(name, expr) for name, expr in config['excluded'].items()]

        for name in names:
            dev, attr = name.split('.')
            cfg = dict(config[name])
            kind = cfg.pop('kind')
            alias = cfg.pop('alias', name)
            if kind == 'iterator':
                it = IterExpression(dev, attr, alias, cfg["expr"], shared)
            elif kind == 'map':
                nmax = cfg.pop('nmax', 1)
                it = Map(dev, attr, alias, cfg, shared, nmax)

            iterators.append(it)

        return cls(iterators, shared,  tuple(excluded))


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



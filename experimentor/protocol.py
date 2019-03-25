from itertools import product
from collections import defaultdict
import time
import ast
from .methods import method_map
# from .iterators import Map, Procedure, IterExpression, Exclusion
# import iterators


def lazy_product(iters):
    if not iters:
        yield ()
    else:
        for it in iters[0]:
            for rest in lazy_product(iters[1:]):
                yield (it,) + rest
                
class Protocol:
    def __init__(self, protocol, context):
        self.protocol = protocol
        self.context = context
    
    @classmethod
    def from_config_file(cls, path, context={}):
        import configparser
        config = configparser.ConfigParser(delimiters=(':'))
        config.read(path)
        protocol = []
        
        for heading in config.sections():
            method, *args = heading.split(':')
            kwargs = dict(config[heading])
            it = method_map[method](context, *args, **kwargs)
            protocol.append(it)
        return cls(protocol, context)

    def __iter__(self):
        self.context['state_idx'] = 0
        self.context['timestamp'] =  int(time.time())
        self.context['data_dir'] = self.context.get('data_dir', '.')

        for param_list in lazy_product(self.protocol):
            state = defaultdict(dict)
            procedures = []
            for method, *params in param_list:
                if method in ['iterate', 'map'] and len(params)==3:
                    dev, attr, val = params
                    state[dev][attr] = val
                
                elif method == 'procedure' and params is not None:
                    procedures.append(params)

                elif method == 'exclude':
                    if None in params:
                        continue
                    else:
                        name, expr = params
                        # self.logger.info(f"skipping state due to {name}, {expr}")
                        break
                
            else:
                self.context['state_idx'] += 1
                yield state, procedures

            self.context['timestamp'] = int(time.time())

import time

class Turtle:
    @classmethod
    def from_protocol(cls, protocol):
        if len(protocol)>1:
            turtle = cls.from_protocol(protocol[1:])
        else:
            turtle = None
        return cls(*protocol[0], turtle=turtle)

    @classmethod
    def from_protocol_file(cls, path):
        import configparser
        config = configparser.ConfigParser(delimiters=(':'))
        config.read(path)
        protocol = []
        for heading in config.sections():
            method, *args = heading.split(':')
            kwargs = dict(config[heading])
            protocol.append((method, args, kwargs))
        return cls.from_protocol(protocol)
            
    @staticmethod
    def iterate(context, alias, dev, attr, expr='[]'):
        for val in eval(expr.format(**context)):
            context = {alias: val}
            state = {dev: {attr: val}}
            yield context, state

    @staticmethod
    def procedure(context, alias, expr, **stages):
        if not eval(expr.format(**context)):
            yield {}, {}
        ps = context.get("procudures", {})
        p = []
        for idx, stage in stages.items():
            method, prop, val_expr = stage.replace(' ', '').split(",")
            dev, attr = prop.split('.')
            val = val_expr.format(**context)
            p.append((method, dev, attr, val))
        ps[alias] = p
        yield {"procudures": ps}, {}

    @staticmethod
    def map(context, alias, dev, attr, nmax=1, **mappings):
        vals = []
        nmax = int(nmax)
        for expr, val_expr in mappings.items():
            if eval(expr.format(**context)):
                try:
                    val = eval(val_expr.format(**context))
                except:
                    val = val_expr.format(**context)
                
                vals.append(val)
        for val in vals[:nmax]:
            context = {alias: val}
            state = {dev: {attr: val}}
            yield context, state
    
    @staticmethod
    def skip(context, **conditions):
        for name, expr in conditions.items():
            if eval(expr.format(**context)):
                return
        else:
            yield context, {}

    @staticmethod
    def count(context):
        cnt = context.get("count", -1)
        yield {"count": cnt+1}, {}

    @staticmethod
    def timestamp(context):
        ts = int(time.time())
        yield {"timestamp": ts}, {}

    def __init__(self, method, args, kwargs, turtle=None):
        self.method = method
        self.args = args
        self.kwargs = kwargs
        self.turtle = turtle

    def states(self, context):
        for my_context, my_state in getattr(self, self.method)(context, *self.args, **self.kwargs):
            new_context = dict(context, **my_context)
            if self.turtle is None:
                yield new_context, my_state
            else:
                for turtle_context, turtle_state in self.turtle.states(new_context):
                    new_state = dict(my_state, **turtle_state)
                    new_context.update(turtle_context)
                    yield new_context, new_state

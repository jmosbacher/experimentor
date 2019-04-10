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
    def count(context, start=0):
        def increment(ctx):
            cnt = ctx.get('count', start-1)
            return {"count": cnt+1 }
        ground_floor = [increment]+ context.get('ground_floor', [])
        yield {"count": start-1, 'ground_floor': ground_floor }, {}

    @staticmethod
    def timestamp(context):
        def timestamp(context):
            return {"timestamp": int(time.time())}
        ground_floor = [timestamp]+ context.get('ground_floor', [])
        ctx = timestamp(context)
        ctx.update(ground_floor=ground_floor)
        yield ctx, {}

    def __init__(self, method, args, kwargs, turtle=None):
        self.method = method
        self.args = args
        self.kwargs = kwargs
        self.turtle = turtle

    def states(self, context):
        for my_context, my_state in getattr(self, self.method)(context, *self.args, **self.kwargs):
            new_context = dict(context, **my_context)
            if self.turtle is None:
                for action in new_context.get('ground_floor', []):
                    ctx = action(new_context)
                    new_context.update(**ctx)
                yield new_context, my_state
            else:
                for turtle_context, turtle_state in self.turtle.states(new_context):
                    new_state = dict(my_state, **turtle_state)
                    new_context.update(turtle_context)
                    yield new_context, new_state
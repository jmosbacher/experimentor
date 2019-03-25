

class Iterate:
    def __init__(self, context, alias, dev, attr, **kwargs):
        self.context = context
        self.alias = alias
        self.dev = dev
        self.attr = attr
        self.expr = kwargs.get("expr", "[]")

    def __iter__(self):
        for val in eval(self.expr.format(**self.context)):
            self.context[self.alias] = val
            yield 'iterate', self.dev, self.attr, val

class Map:
    def __init__(self, context, alias, dev, attr, nmax=1, **mappings):
        # nmax = mappings.pop("nmax", 1)
        self.context = context
        self.alias = alias
        self.dev = dev
        self.attr = attr
        self.nmax = int(nmax)
        self.mappings = mappings

    def __iter__(self):
        vals = []
        for expr, val_expr in self.mappings.items():
            if eval(expr.format(**self.context)):
                try:
                    val = eval(val_expr.format(**self.context))
                except:
                    val = val_expr.format(**self.context)
                
                vals.append(val)
        for val in vals[:self.nmax]:
            self.context[self.alias] = val
            yield 'map', self.dev, self.attr, val
        
class Procedure:
    def __init__(self, context, alias, expr, **protocol):
        self.context = context
        self.alias = alias
        self.expr = expr
        self.protocol = protocol

    def __iter__(self):
        if eval(self.expr.format(**self.context)):
            proc = []
            for k,v in self.protocol.items():
                if " = " in v:
                    prop, expr = v.split(" = ")
                elif "=" in v:
                    prop, expr = v.split("=")
                else:
                    raise AttributeError("Bad assignment instruction, use = symbol")
                dev, attr = prop.split(".")
                proc.append((dev, attr, eval(expr.format(**self.context))) )
                
            yield 'procedure', self.alias, proc
        else:
            yield 'procedure', None

class Exclude:
    def __init__(self, context, **conditions):
        self.context = context
        self.conditions = conditions
    def __iter__(self):
        for name, expr in self.conditions.items():
            if eval(expr.format(**self.context)):
                yield 'exclude', name, expr.format(**self.context)
                break
        else:
            yield 'exclude', None

method_map = {
    "iterate" : Iterate,
    "map": Map, 
    "procedure": Procedure,
    "exclude": Exclude,
}
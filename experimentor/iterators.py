
class Map:
    def __init__(self, dev, attr, alias, map, shared_state, nmax=1):
        self.dev = dev
        self.attr = attr
        self.alias = alias
        self.map = map
        self.shared_state = shared_state
        self.nmax = nmax

    def __iter__(self):
        vals = []
        for expr, val in self.map.items():
            if eval(expr.format(**self.shared_state)):
                vals.append(val)
                if len(vals) >= self.nmax:
                    break

        for val in vals:
            self.shared_state[self.alias] = val
            yield self.dev, self.attr, val


class IterExpression:
    def __init__(self, dev, attr, alias, expr, shared_state):
        self.dev = dev
        self.attr = attr
        self.alias = alias
        self.expr = expr
        self.shared_state = shared_state

    def __iter__(self):
        for val in eval(self.expr.format(**self.shared_state)):
            self.shared_state[self.alias] = val
            yield self.dev, self.attr, val

class Eval:
    def __init__(self, dev, attr, alias, expr, shared_state):
        self.dev = dev
        self.attr = attr
        self.alias = alias
        self.expr = expr
        self.shared_state = shared_state

    def __iter__(self):
        val = eval(self.expr.format(**self.shared_state))
        self.shared_state[self.alias] = val
        yield self.dev, self.attr, val


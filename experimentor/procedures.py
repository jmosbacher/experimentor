import time


class Procedure:
    def __init__(self, name, global_condition, steps):
        self.name = name
        self.global_condition = global_condition
        self.steps = steps

    @staticmethod
    def set(system, context, prop, val_expr):
        dev, attr = prop.split('.')
        val = val_expr.format(**context)
        system[dev][attr] = val
    
    @staticmethod
    def wait(system, context, prop, val_expr):
        dev, attr = prop.split('.')
        val = val_expr.format(**context)
        while system[dev][attr] != val:
            time.sleep(0.05)
            
    def perform(self, system, context):
        if not eval(self.global_condition.format(**context)):
            return
        for condition, method, args in self.steps:
            if eval(condition.format(**context)):
                getattr(self, method)(system, context, *args)


class Procedures:
    def __init__(self, procedures):
        self.procedures = procedures
        
    @classmethod
    def from_procedures_file(cls, path):
        import configparser
        config = configparser.ConfigParser(delimiters=(':'))
        config.read(path)
        procedures = []
        for heading in config.sections():
            name, global_condition = heading.split(':')
            steps = []
            for condition, arg_expr in dict(config[heading]).items():
                method, *args = arg_expr.split('->')
                steps.append((condition, method, args))
            p = Procedure(name, global_condition, steps)
            procedures.append(p)
        return cls(procedures)

    def perform(self, system, context):
        for proc in self.procedures:
            proc.perform(system, context)
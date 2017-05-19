

class Environ(dict):

    def append(self, name, value):
        existing = self.get(name, None)
        if existing is None:
            self[name] = value
        else:
            self[name] = '%s:%s' % (existing, value)

    def prepend(self, name, value):
        existing = self.get(name, None)
        if existing is None:
            self[name] = value
        else:
            self[name] = '%s:%s' % (value, existing)


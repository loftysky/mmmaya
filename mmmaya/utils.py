

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

    def remove(self, name, value, strict=True):
        existing = self.get(name, None)
        if not existing:
            raise KeyError(name)
        before = existing.split(':')
        after = [x for x in before if x != value]
        if before == after:
            if strict:
                raise ValueError(value)
            return 0
        self[name] = ':'.join(after)
        return len(before) - len(after)


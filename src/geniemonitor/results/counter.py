import collections

from functools import total_ordering

RESULT_KEYS = ('ok',
               'warning', 
               'critical', 
               'errored',
               'partial')

@total_ordering
class StatusCounter(collections.MutableMapping):
    '''StatusCounter class

    A standard dictionary keeping track of overall health status.
    By default, contains the following keys:

        ok, warning, critical, errored, partial

    '''


    def __init__(self, results = None):

        self.data = dict()

        if results:
            self.data.update(results)

        for key in RESULT_KEYS:
            self.data.setdefault(key, 0)

    def __getitem__(self, name):
        return self.data.__getitem__(name)

    def __setitem__(self, name, value):
        return self.data.__setitem__(name, value)

    def __getattr__(self, name):
        if name in self.data:
            return self.data[name]
        else:
            raise AttributeError("'%s' has no attribute '%s'" % 
                                 (type(self).__name__, name))

    def __setattr__(self, name, value):
        if name == 'data':
            super().__setattr__(name, value)
        else:
            self.data[name] = value

    def __delitem__(self, name):
        if name in RESULT_KEYS:
            self.data[name] = 0
        else:
            self.data.__delitem__(name)
    
    def __str__(self):
        strdata = self.data.copy()
        return str(strdata)

    def __repr__(self):
        reprdata = self.data.copy()
        return repr(reprdata)

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, key):
        return key in self.data

    def __len__(self):
        return len(self.data)

    def copy(self):
        return type(self)(results = self.data.copy())

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

    def update(self, *args, **kwargs):
        self.data.update(*args, **kwargs)

    def __lt__(self, other):
        if type(self) == type(other):
            return self.data.__lt__(other.data)
        else:
            return self.data.__lt__(other)

    def __eq__(self, other):
        if type(self) == type(other):
            return self.data.__eq__(other.data)
        else:
            return self.data.__eq__(other)

    def __reduce__(self):
        return self.__class__, (self.data,)

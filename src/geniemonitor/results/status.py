
from .utils import massage_meta

class HealthStatus(object):
    '''Health Status class

        +-----------------------------+------------------+------------------+
        | Object                      | Code             | String           |
        +=============================+==================+==================+
        | OK                          | 0                | 'ok'             |
        +-----------------------------+------------------+------------------+
        | Warning                     | 1                | 'warning'        |
        +-----------------------------+------------------+------------------+
        | Critical                    | 2                | 'critical'       |
        +-----------------------------+------------------+------------------+
        | Errored                     | 3                | 'errored'        |
        +-----------------------------+------------------+------------------+
        | Partial                     | 4                | 'partial'        |
        +-----------------------------+------------------+------------------+
        | Null                        | 99               | 'null'           |
        +-----------------------------+------------------+------------------+

    Result Rollup:
        status objects can be rolled up together by using the addition "+"
        operator. Eg:

        producer + OK  -> producer

    Note:
        - Null is a special object, representing "no status".

    '''
    
    # internal dict for controlling the roll up behaviors
    __rollup__ = { 'ok'      : { 'ok'      : 'ok',
                                 'warning' : 'warning',
                                 'critical': 'critical',
                                 'errored' : 'errored',
                                 'partial' : 'partial',
                                 'null'    : 'warning'},
                   'warning' : { 'ok'      : 'warning',
                                 'warning' : 'warning',
                                 'critical': 'critical',
                                 'errored' : 'errored',
                                 'partial' : 'warning',
                                 'null'    : 'warning'},
                   'critical': { 'ok'      : 'critical',
                                 'warning' : 'critical',
                                 'critical': 'critical',
                                 'errored' : 'errored',
                                 'partial' : 'critical',
                                 'null'    : 'critical'},
                   'errored' : { 'ok'      : 'errored',
                                 'warning' : 'errored',
                                 'critical': 'errored',
                                 'errored' : 'errored',
                                 'partial' : 'errored',
                                 'null'    : 'errored'},
                   'partial' : { 'ok'      : 'partial',
                                 'warning' : 'warning',
                                 'critical': 'critical',
                                 'errored' : 'errored',
                                 'partial' : 'partial',
                                 'null'    : 'partial'},
                   'null'    : { 'ok'      : 'ok',
                                 'warning' : 'warning',
                                 'critical': 'critical',
                                 'errored' : 'errored',
                                 'partial' : 'partial',
                                 'null'    : 'null'},
                 }

    # mapping between result code and message
    __code_map__ = {  0: 'ok',
                      1: 'warning',
                      2: 'critical',
                      3: 'errored',
                      4: 'partial',
                     99: 'null', }

    # mapping between result string and code
    __str_map__ = {v: k for k,v in __code_map__.items()}

    @classmethod
    def from_str(cls, string):
        '''classmethod from_str

        Allows the creation of HealthStatus objects from strings names

        Arguments:
            string (str): string name to convert to objects
        '''

        return cls(cls.__str_map__[string.lower()])

    def __init__(self, code = None, meta = {}, status = None):
        '''built-in __init__

        Inits internal variables: name and code

        Arguments:
            code (int): code of new HealthStatus obj.
        '''

        self.code = code or status.code if status else code
        self.name = self.__code_map__[self.code]

        self._meta = massage_meta(meta)

    def __call__(self, meta = {}):
        '''built-in __call__

        Returns a new health status instance with the provided meta
        '''
        return HealthStatus(code = self.code, meta = meta)

    @property
    def meta(self):
        return self._meta

    @meta.setter
    def meta(self, value):
        self._meta.update(massage_meta(value))

    def __bool__(self):
        '''built-in __bool__

        supports bool() checking of result objects.

        Returns:
            True for result object OK
            False otherwise
        '''
        if self.name == 'ok':
            return True
        else:
            return False

    def __eq__(self, other):
        if not isinstance(other, HealthStatus):
            return False
        return self.code == other.code

    def __int__(self):
        '''built-in __int__

        Returns the numeric (ats code) of this HealthStatus object
        '''
        return self.code

    def __add__(self, other):
        '''built-in __add__

        Adds this result to another result object. Enables rollup of results.

        Example:
            Failed + Errored
        '''
        if not isinstance(other, HealthStatus):
            other = HealthStatus(code = 0, meta = other or {})

        rollup = self.__rollup__[self.name][other.name]

        meta = self.meta.copy()
        meta.update(other.meta)

        return HealthStatus(code = self.__str_map__[rollup], meta = meta)

    def __radd__(self, other):
        '''built-in __radd__

        Reverse add this result to another result object. Allows sum() operation
        without having to specify a default null value.

        Note:
            When Python tries to evaluate x + y it first attempts to call 
            x.__add__(y). If this fails then it falls back to y.__radd__(x).

        Example:
            0 + Errored
        '''
        if not isinstance(other, HealthStatus):
            other = HealthStatus(code = 0, meta = other or {})

        meta = self.meta.copy()
        meta.update(other.meta)

        if other is 0:
            return HealthStatus(code = self.code,
                                meta = meta)
        else:
            rollup = self.__rollup__[other.name][self.name]
            return HealthStatus(code = self.__str_map__[rollup],
                                meta = meta)

    def __str__(self):
        '''built-in __int__

        Returns the string name (ats result string) of this HealthStatus object
        '''
        return self.name

    def __repr__(self):
        return self.name.capitalize()

    def __getnewargs__(self):
        return (self.code, {})

    def __lt__(self, other):
        return self.code < other.code

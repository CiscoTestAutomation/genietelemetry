


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

    # container for controlling object creation & uniqueness
    __objects__ = {}

    @classmethod
    def from_str(cls, string):
        '''classmethod from_str

        Allows the creation of HealthStatus objects from strings names

        Arguments:
            string (str): string name to convert to objects
        '''

        return cls(cls.__str_map__[string.lower()])

    def __new__(cls, code):
        '''built-in __new__

        Returns the same HealthStatus object if the given code was already 
        created somewhere.

        Arguments:
            code (int): code of new HealthStatus obj.
        '''
        if code in cls.__objects__:
            return cls.__objects__[code]
        else:
            cls.__objects__[code] = super().__new__(cls)
            return cls.__objects__[code]

    def __init__(self, code):
        '''built-in __init__

        Inits internal variables: name and code

        Arguments:
            code (int): code of new HealthStatus obj.
        '''

        self.code = code
        self.name = self.__code_map__[code]

    def __bool__(self):
        '''built-in __bool__

        supports bool() checking of result objects.

        Returns:
            True for result object Normal and Null
            False otherwise
        '''
        if self.name == 'normal':
            return True
        else:
            return False

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
        rollup = self.__rollup__[self.name][other.name]
        return HealthStatus(self.__str_map__[rollup])

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

        if other is 0:
            return self
        else:
            rollup = self.__rollup__[other.name][self.name]
            return HealthStatus(self.__str_map__[rollup])

    def __str__(self):
        '''built-in __int__

        Returns the string name (ats result string) of this HealthStatus object
        '''
        return self.name

    def __repr__(self):
        return self.name.capitalize()

    def __getnewargs__(self):
        return (self.code,)

    def __lt__(self, other):
        return self.code < other.code

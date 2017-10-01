import weakref

class ContextReporter(object):
    '''ContextReporter

    A context reporter is a reporter that can be used as a context manager. It
    automatically registers/reports/logs the start and end of content running
    within it, and is naturally used to report on events, activities and results
    of this content.

    A context reporter is designed as a nested chain of parent-child
    relationship. Each reporter could have a parent, and each children is 
    instanciated through the the parent's child() api. This api is essentially
    an injection point allowing subclasses to implement their own parent/child
    relationship.

    When a context reporter has a parent, it automatically gain the ability to
    access its parent's (and subsequently, all parent's parents) attribute as 
    its own attributes without having to explicitly state self.parent.<attr>.

    '''

    def __init__(self, parent = None):

        # this reporter's parent
        self.parent = parent

        # list of children reports
        self.children = []

    @property
    def parent(self):
        return None if self._parentref is None else self._parentref()

    @parent.setter
    def parent(self, obj):
        if obj is None:
            self._parentref = None
        else:
            self._parentref = weakref.ref(obj)

            # register to parent as children
            obj.children.append(self)

    @property
    def parents(self):
        parents = []

        obj = self
        while obj.parent is not None:
            parents.append(obj.parent)
            obj = obj.parent

        return parents

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    @property
    def __enter__(self):
        'redirect context mgmt __enter__ to start()'
        return self.start

    @property
    def __exit__(self):
        'redirect context mgmt __enter__ to stop()'
        return self.stop

    def child(self):
        return ContextReporter(parent = self)

    def __getattr__(self, attr):
        '''
        magic, chain attribute getting to include parent attributes
        '''
        
        if hasattr(self.parent, attr):
            return getattr(self.parent, attr)
        else:
            raise AttributeError("'%s' object has no attribute '%s"
                                 % (self.__class__.__name__, attr))
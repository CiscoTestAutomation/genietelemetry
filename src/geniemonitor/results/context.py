from .status import HealthStatus


class HealthStatusContext(object):
    '''HealthStatusContext class

    Not intended to be used by itself.

    HealthStatusContext class is a context container that its subclasses to have
    statuss, and enables the use of python 'with' statement, propagating statuss
    from one context to another.

    GenieMonitor HealthStatus base classes inherits this class, giving them the
    ability to carry a status.

    Pseudo Code Example::

        obj_a = HealthStatusContext()
        obj_b = HealthStatusContext()
        # roll up obj_b's status context into obj_a automatically.
        with obj_a:
            with obj_b:
                obj_b.status = Failed
    '''

    def __init__(self,
                 status = HealthStatus(99),
                 propagate_status = True,
                 *args,
                 **kwargs):
        '''built-in __init__

        Arguments:
            status (HealthStatus): the default status for this context.
                                 Defaults to: Null (no status)
            propagate_status (bool): whether status from this context should
                                     propagate to its parent context.
                                     Defaults to: True
            ``*args``, ``**kwargs``:
            any other arguments will be propagated through.
        '''

        self.status = status
        self._propagate_status = propagate_status

        super().__init__(*args, **kwargs)

    def __enter__(self):
        '''built-in __enter__

        adds this context object to the context stack

        '''
        f = getattr(super(), '__enter__', None)
        enter_status = f() if f else self
        __context_stack__.append(self)
        return enter_status

    def __exit__(self, *exc_info):
        '''built-in __exit__

        removes this context from the context stack, roll up status to parent
        if necessary

        '''
        assert get_status_context() is self

        __context_stack__.pop()

        if self._propagate_status:
            update_health_status(self.status)

        f = getattr(super(), '__exit__', None)

        return f(*exc_info) if f else False


class RootHealthStatusContext(HealthStatusContext):
    '''RootHealthStatusContext class

    Special instance of HealthStatusContext, serving as the root context of all
    subsequent contexts
    '''
    pass

# internal variable containing the global context stack
# root context is always created as the number 1
__context_stack__ = [RootHealthStatusContext(), ]


def get_status_context(predicate=None):
    for ctx in reversed(__context_stack__):
        if predicate is None or predicate(ctx):
            return ctx

def update_health_status(status):
    ctx = get_status_context()
    ctx.status += status
    return ctx.status

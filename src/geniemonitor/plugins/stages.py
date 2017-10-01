from enum import Enum

# declare module as infra
__genie_monitor_infra__ = True

class Scope(Enum):
    execution = 'execution'

# define valid plugin stages
class PluginStage(Enum):
    pre_execution = 'pre_execution'
    execution = "execution"
    post_execution = 'post_execution'

    @property
    def is_pre(self):
        return self.value.startswith('pre')

    @property
    def is_post(self):
        return self.value.startswith('post')

    @property
    def is_execution(self):
        return self.value.startswith('execution')

    @property
    def scope(self):
        return Scope(self.value.split('_')[-1])

    @property
    def counterpart(self):
        if self.is_pre:
            return self.__class__(self.value.replace('pre', 'post'))
        else:
            return self.__class__(self.value.replace('post', 'pre'))

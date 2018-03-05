# default configuration for GenieTelemetry
# (removed file loading for simplicity)
DEFAULT_CONFIGURATION = '''
plugins:
    crashdumps:
        interval: 60
        enabled: True
        module: genietelemetry_libs.plugins.crashdumps
    tracebackcheck:
        interval: 60
        enabled: True
        module: genietelemetry_libs.plugins.tracebackcheck

manager:
    class: genietelemetry.manager.TimedManager

'''

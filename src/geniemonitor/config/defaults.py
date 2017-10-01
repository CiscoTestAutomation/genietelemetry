# default configuration for GenieMonitor
# (removed file loading for simplicity)
DEFAULT_CONFIGURATION = '''
plugins:
    crashdumps:
        interval: 30
        enabled: True
        module: geniemonitor.plugins.crashdumps

core:
    job:
        class: geniemonitor.job.Job
    reporter:
        class: geniemonitor.reporter.HealthReporter
    runinfo:
        class: geniemonitor.runinfo.RunInfo
    producer:
        class: geniemonitor.processor.DataProducer
    consumer:
        class: geniemonitor.processor.DataConsumer
    connection:
        class: unicon.Unicon
    thresholds:
        OK: 272h
        Warning: 252h
        Critical: 248h
'''
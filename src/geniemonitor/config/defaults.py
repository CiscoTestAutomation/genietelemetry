# default configuration for GenieMonitor
# (removed file loading for simplicity)
DEFAULT_CONFIGURATION = '''
plugins:
    keepalive:
        interval: 30
        enabled: True
        module: geniemonitor.plugins.keepalive
    crashdumps:
        interval: 60
        enabled: True
        module: geniemonitor.plugins.crashdumps

core:
    job:
        class: geniemonitor.job.Job
    reporter:
        class: geniemonitor.reporter.HealthReporter
    runinfo:
        class: geniemonitor.runinfo.RunInfo
    mailbot:
        class: geniemonitor.email.MailBot
    producer:
        class: geniemonitor.processor.DataProducer
    consumer:
        class: geniemonitor.processor.DataConsumer
    switch:
        class: geniemonitor.switch.Switch
    connection:
        class: unicon.Unicon
    thresholds:
        OK: 372h
        Warning: 352h
        Critical: 348h
'''
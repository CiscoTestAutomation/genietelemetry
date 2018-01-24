# default configuration for GenieTelemetry
# (removed file loading for simplicity)
DEFAULT_CONFIGURATION = '''
plugins:
    keepalive:
        interval: 30
        enabled: True
        module: genietelemetry_libs.plugins.keepalive
    crashdumps:
        interval: 60
        enabled: True
        module: genietelemetry_libs.plugins.crashdumps
    tracebackcheck:
        interval: 60
        enabled: True
        module: genietelemetry_libs.plugins.tracebackcheck

core:
    job:
        class: genietelemetry.job.Job
    reporter:
        class: genietelemetry.reporter.HealthReporter
    runinfo:
        class: genietelemetry.runinfo.RunInfo
    mailbot:
        class: genietelemetry.email.MailBot
    producer:
        class: genietelemetry.processor.DataProducer
    consumer:
        class: genietelemetry.processor.DataConsumer
    switch:
        class: genietelemetry.switch.Switch
    connection:
        class: unicon.Unicon
    thresholds:
        OK: 72h
        Warning: 48h
        Critical: 24h
'''

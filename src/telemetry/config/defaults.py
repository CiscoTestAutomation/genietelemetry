# default configuration for Telemetry
# (removed file loading for simplicity)
DEFAULT_CONFIGURATION = '''
plugins:
    keepalive:
        interval: 30
        enabled: True
        module: telemetry_libs.plugins.keepalive
    crashdumps:
        interval: 60
        enabled: True
        module: telemetry_libs.plugins.crashdumps
    tracebackcheck:
        interval: 60
        enabled: True
        module: telemetry_libs.plugins.tracebackcheck

core:
    job:
        class: telemetry.job.Job
    reporter:
        class: telemetry.reporter.HealthReporter
    runinfo:
        class: telemetry.runinfo.RunInfo
    mailbot:
        class: telemetry.email.MailBot
    producer:
        class: telemetry.processor.DataProducer
    consumer:
        class: telemetry.processor.DataConsumer
    switch:
        class: telemetry.switch.Switch
    connection:
        class: unicon.Unicon
    thresholds:
        OK: 72h
        Warning: 48h
        Critical: 24h
'''

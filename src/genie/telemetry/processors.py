import sys
import logging

# runtime
from ats.easypy import runtime

# aetest
from ats.aetest import CommonSetup, CommonCleanup

from genie.telemetry import Manager
from genie.telemetry.config import DEFAULT_CONFIGURATION

logger = logging.getLogger(__name__)

def prepostprocessor(section):
    '''Check for genie telemetry plugins specified by the user in the
    genie_telemetry plugins provided.
    '''

    ancestor = getattr(section, 'parent', section)
    while getattr(ancestor, 'parent', None):
        ancestor = ancestor.parent

    if not section or not ancestor:
        return

    common_section = isinstance(section, (CommonSetup, CommonCleanup))

    # Check for the trigger parameter only if the section is a trigger
    # Case where 'genie_telemetry' is not enabled for the trigger
    if not common_section and not section.parameters.get('genie_telemetry',
                                                         False):
        logger.info("Skipping 'genie.telemetry' processor since it "
                    "genie_telemetry flag is set to False.")
        return

    genie_telemetry = getattr(ancestor, 'genie_telemetry', None)
    try:
        # Instantiate the Manager
        if not genie_telemetry:

            testbed = section.parameters.get('testbed', runtime.testbed)
            if not testbed:
                logger.info("Skipping 'genie.telemetry' processor : "
                            "no testbed supplied")
                return

            # if --genietelemetry is not supplied, fallback to default
            # configuration
            configuration = Manager.parser.parse_args().configuration

            kwargs = dict(runinfo_dir=runtime.runinfo.runinfo_dir,
                          configuration=configuration or DEFAULT_CONFIGURATION)

            genie_telemetry = ancestor.genie_telemetry = Manager(testbed,
                                                                 **kwargs)

        uid = str(getattr(section, 'uid', section))

        kwargs = dict()
        # Check for the section specific plugins to run with
        telemetry_plugins = section.parameters.get('telemetry_plugins', [])
        # Run only specified plugins
        if telemetry_plugins:
            kwargs['plugins'] = telemetry_plugins

        # Run all plugins on the section (CS/Trigger/CC)
        genie_telemetry.run(uid, **kwargs)

        # Checking the execution result
        anomallies = []
        # iterating over plugin, results
        results = genie_telemetry.results.get(uid, {})
        for pluginname, devices in results.items():

            results = []
            # iterating over device, result
            for name, result in devices.items():
                status = result.get('status', None)
                status_name = getattr(status, 'name', status)
                if str(status_name).lower() == 'ok':
                    continue
                results.append('\n\t\t'.join([name, status_name]))
            # everything is ok
            if not results:
                continue

            anomallies.append('\n\t'.join([pluginname, '\n'.join(results)]))

        if isinstance(section, CommonCleanup):
            # Calling finalize_report
            genie_telemetry.finalize_report()

    except Exception as e:
        if common_section:
            logger.info("Skipping 'genie.telemetry' processor since it "
                        "encountered an issue: {error}".format(error=e))
            return
        else:
            section.skipped("'genie.telemetry' encountered an issue: {}".\
                format(e))

    # Determine section result as per genie.telemetry findings
    if anomallies:
        section.passx("'genie.telemetry' caught anomallies: \n{}".format(
                                                      '\n'.join(anomallies))
                                                    )

import sys
import logging
from copy import copy

# runtime
from ats.easypy import runtime

# aetest
from ats.aetest import CommonSetup, CommonCleanup

from genie.telemetry import Manager

logger = logging.getLogger(__name__)

def genie_telemetry_processor(section):
    '''Check for genie telemetry plugins specified by the user in the
    genie_telemetry plugins provided.
    '''

    ancestor = getattr(section, 'parent', section)
    while getattr(ancestor, 'parent', None):
        ancestor = ancestor.parent

    if not section or not ancestor:
        return

    common_section = isinstance(section, (CommonSetup, CommonCleanup))
    genie_telemetry = getattr(ancestor, 'genie_telemetry', None)

    # validate --genietelemetry configuration
    args = copy(sys.argv)
    configuration = Manager.parser.parse_args(args).configuration
    if not configuration and not genie_telemetry:
        logger.info("Skipping 'genie.telemetry' processor as '--genietelemetry'"
                    " argument is not provided.")
        return

    # by default genie_telemetry is enabled
    # if 'genie_telemetry' is specifically disabled, skip
    if not section.parameters.get('genie_telemetry', True):
        logger.info("Skipping 'genie.telemetry' processor since it "
                    "genie_telemetry parameter is set to False.")
        return

    try:
        # Instantiate the Manager
        if not genie_telemetry:

            testbed = section.parameters.get('testbed', runtime.testbed)
            if not testbed:
                logger.info("Skipping 'genie.telemetry' processor : "
                            "no testbed supplied")
                return

            kwargs = dict(runinfo_dir=runtime.runinfo.runinfo_dir,
                          configuration=configuration)

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

            p_results = []
            # iterating over device, result
            for name, result in devices.items():
                status = result.get('status', None)
                status_name = getattr(status, 'name', status)
                if str(status_name).lower() == 'ok':
                    continue
                p_results.append('\n\t\t'.join([name, status_name]))
            # everything is ok
            if not p_results:
                continue

            anomallies.append('\n\t'.join([pluginname, '\n'.join(p_results)]))

        if isinstance(section, CommonCleanup):
            # Calling finalize_report
            genie_telemetry.finalize_report()

    except Exception as e:
        if common_section:
            logger.info("Skipping 'genie.telemetry' processor since it "
                        "encountered an issue: {error}".format(error=e))
            return
        else:
            section.passx("'genie.telemetry' encountered an issue: {}".\
                          format(e))

    # Determine section result as per genie.telemetry findings
    if anomallies:
        section.passx("'genie.telemetry' caught anomallies: \n{}".format(
                                                      '\n'.join(anomallies))
                                                    )

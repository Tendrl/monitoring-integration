import datetime
import os
import shutil
import stat

from tendrl.commons import flows
from tendrl.commons.flows.exceptions import FlowExecutionFailedError
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana \
    import alert_utils as grafana_utils
from tendrl.monitoring_integration.graphite import graphite_utils


class DeleteMonitoringData(flows.BaseFlow):
    def __init__(self, *args, **kwargs):
        super(DeleteMonitoringData, self).__init__(*args, **kwargs)

    def run(self):
        integration_id = self.parameters.get("TendrlContext.integration_id")
        delete_telemetry_data = self.parameters.get(
            "Cluster.delete_telemetry_data"
        )
        # Delete the cluster related alert dashboards
        grafana_utils.delete_panel(integration_id)

        # Remove any symlink created for cluster
        _cluster = NS.tendrl.objects.Cluster(
            integration_id=integration_id
        ).load()
        if _cluster.short_name not in [None, ""]:
            symlink_path = "%snames/%s" % (
                graphite_utils.get_data_dir_path(),
                _cluster.short_name
            )
            if os.path.islink(symlink_path):
                os.unlink(symlink_path)

        # Archive the carbon data for the cluster
        archive_base_path = "%s/archive/clusters" % (
            NS.config.data.get(
                "graphite_archive_path",
                graphite_utils.get_data_dir_path(),
            )
        )

        if _cluster.short_name not in [None, ""]:
            cluster_short_name = _cluster.short_name
        else:
            cluster_short_name = integration_id
        archive_path = "%s/%s_%s" % (
            archive_base_path,
            cluster_short_name,
            str(
                datetime.datetime.now().isoformat()
            ).replace(".", ":")
        )
        resource_path = "%s/clusters/%s" % \
            (
                graphite_utils.get_data_dir_path(),
                integration_id
            )
        # if source path not exist then no need to archive and raise
        # exception, because it will affect when user try to do
        # unmanage flow after import flow fail
        if os.path.exists(resource_path):
            if not os.path.exists(archive_base_path):
                try:
                    os.makedirs(str(archive_base_path))
                except OSError as ex:
                    logger.log(
                        "error",
                        NS.publisher_id,
                        {
                            "message": "Failed to create archive dir:"
                            " (%s)" % ex
                        },
                        job_id=self.parameters.get('job_id'),
                        flow_id=self.parameters.get('flow_id'),
                        integration_id=integration_id
                    )
                    raise FlowExecutionFailedError(
                        "Failed to create archive dir: (%s)"
                        "for monitoring data. Error: (%s)" %
                        (str(archive_base_path), ex)
                    )

            # Currently default is not to delete the telemetry data
            # This is a stop gap and ideally delete_telemetry_data
            # should be set as yes by default. This logic should be
            # changed later to make the same in effect.
            if delete_telemetry_data and delete_telemetry_data == "yes":
                def remove_readonly(func, path, excinfo):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                shutil.rmtree(resource_path, onerror=remove_readonly)
                # Log an event mentioning the removal
                logger.log(
                    "debug",
                    NS.publisher_id,
                    {
                        "message": "%s un-managed.\n"
                        "Removed monitoring data %s" %
                        (integration_id, resource_path)
                    }
                )
            else:
                try:
                    shutil.move(resource_path, archive_path)
                except Exception as ex:
                    if type(ex) == IOError:
                        logger.log(
                            "error",
                            NS.publisher_id,
                            {
                                "message": "Failed to archive the monitoring "
                                "data. Error: (%s)" % ex
                            },
                            job_id=self.parameters.get('job_id'),
                            flow_id=self.parameters.get('flow_id'),
                            integration_id=integration_id
                        )
                    raise FlowExecutionFailedError(
                        "Failed to archive the monitoring data. Error: (%s)" %
                        ex
                    )

                # Log an event mentioning the archive data location
                logger.log(
                    "debug",
                    NS.publisher_id,
                    {
                        "message": "%s un-managed.\n"
                        "Archived monitoring data to %s" %
                        (integration_id, archive_path)
                    }
                )

        return True

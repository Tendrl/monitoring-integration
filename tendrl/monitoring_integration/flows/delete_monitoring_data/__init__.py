import datetime
import os
import shutil

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

        # Delete the cluster related alert dashboards
        grafana_utils.delete_panel(integration_id)

        # Archive the carbon data for the cluster
        archive_base_path = "%s/clusters" % (
            NS.config.data.get(
                "graphite_archive_path",
                "/usr/share/tendrl/graphite/archive"
            )
        )
        if not os.path.exists(archive_base_path):
            try:
                os.makedirs(str(archive_base_path))
            except OSError as ex:
                raise FlowExecutionFailedError(
                    "Failed to create archive dir: (%s)"
                    "for monitoring data. Error: (%s)" %
                    (str(archive_base_path), ex)
                )
        archive_path = "%s/%s_%s" % (
            archive_base_path,
            integration_id,
            str(datetime.datetime.now().isoformat())
        )
        resource_path = "%s/clusters/%s" % \
            (
                graphite_utils.get_data_dir_path(),
                integration_id
            )
        try:
            shutil.move(resource_path, archive_path)
        except Exception as ex:
            raise FlowExecutionFailedError(
                "Failed to archive the monitoring data. Error: (%s)" %
                ex
            )

        # Log an event mentioning the archive data location
        logger.log(
            "info",
            NS.publisher_id,
            {
                "message": "Cluster %s moved to un-managed state.\n"
                "The archived monitoring data available at: %s" %
                (integration_id, archive_path)
            }
        )

        return True

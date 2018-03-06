from tendrl.commons import flows
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import alert_utils


class UpdateDashboard(flows.BaseFlow):

    def run(self):
        super(UpdateDashboard, self).run()
        resource_name = self.parameters.get("Trigger.resource_name", None)
        if resource_name:
            resource_name = str(resource_name)
        resource_type = str(
            self.parameters.get("Trigger.resource_type")).lower()
        operation = str(self.parameters.get("Trigger.action")).lower()
        integration_id = self.parameters.get("TendrlContext.integration_id")
        if resource_type in alert_utils.GLUSTER_DASHBOARDS:
            # Deleting gluster related alert dashboard
            if operation.lower() == "delete":
                resp = alert_utils.delete_panel(
                    integration_id,
                    alert_utils.GLUSTER_DASHBOARDS[resource_type],
                    resource_name
                )
                if resp.status_code == 200:
                    msg = "Alert dashboard for %s is deleted successfully" % \
                        (resource_name)
                    logger.log("debug", NS.get("publisher_id", None),
                               {'message': msg})
                else:
                    msg = "Alert dashboard delete failed for %s" % \
                        (resource_name)
                    logger.log("debug", NS.get("publisher_id", None),
                               {'message': msg})
            else:
                logger.log("debug", NS.get("publisher_id", None),
                           {'message': "Wrong action"})

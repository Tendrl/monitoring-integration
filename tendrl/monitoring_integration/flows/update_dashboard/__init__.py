import copy

from tendrl.commons import flows
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.flows.update_dashboard import alert_utils
from tendrl.monitoring_integration.grafana.alert_utils import \
    get_alert_dashboard
from tendrl.monitoring_integration.grafana.alert_utils import \
    post_dashboard

GLUSTER_DASHBOARDS = {"host": "nodes",
                      "volume": "volumes",
                      "brick": "bricks"
                      }


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
        if resource_type in GLUSTER_DASHBOARDS:
            # Deleting gluster related alert dashboard
            if operation.lower() == "delete":
                self._delete_panel(
                    integration_id,
                    GLUSTER_DASHBOARDS[resource_type],
                    resource_name
                )
            else:
                logger.log("error", NS.get("publisher_id", None),
                           {'message': "Wrong action"})

    def _delete_panel(self, integration_id,
                      resource_type, resource_name=None):
        response = []
        if resource_name is None:
            # delete all dashboards using integration id
            for dash_name in GLUSTER_DASHBOARDS:
                alert_dashboard = alert_utils.remove_cluster_rows(
                    integration_id,
                    GLUSTER_DASHBOARDS[dash_name]
                )
        else:
            if resource_type == "nodes":
                resource_name = resource_name.replace(".", "_")
            alert_dashboard = get_alert_dashboard(resource_type)
            alert_utils.remove_row(
                alert_dashboard,
                integration_id,
                resource_type,
                resource_name
            )
        resp = post_dashboard(alert_dashboard)
        response.append(copy.deepcopy(resp))
        return response

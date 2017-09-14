import json
import copy


from tendrl.monitoring_integration.flows.update_dashboard.alert_utils import get_alert_dashboard
from tendrl.monitoring_integration.flows.update_dashboard import alert_utils
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.commons import flows
from tendrl.commons.utils import log_utils as logger


class UpdateDashboard(flows.BaseFlow):

    def run(self):
        super(UpdateDashboard, self).run()
        self.map = {"cluster" : "at-a-glance", "host": "nodes", "volume" : "volumes", "brick" : "bricks"}
        resource_name = str(self.parameters.get("Trigger.resource_name")).lower()
        resource_type = str(self.parameters.get("Trigger.resource_type")).lower()
        operation = str(self.parameters.get("Trigger.action")).lower()
        cluster_id = self.parameters.get("TendrlContext.integration_id")
        if operation.lower() == "add":
            self._add_panel(cluster_id, self.map[resource_type], resource_name)
        elif operation.lower() == "delete":
            self._delete_panel(cluster_id, self.map[resource_type], resource_name=None)
        else:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': "Wrong action"})

    def _add_panel(self, cluster_id, resource_type, resource_name=None):
        if resource_type == "nodes":
            resource_name = resource_name.replace(".", "_")
        alert_dashboard = alert_utils.get_alert_dashboard(resource_type)
        if alert_dashboard:
            alert_row = alert_utils.fetch_row(alert_dashboard)
            alert_utils.add_resource_panel(alert_row, cluster_id, resource_type, resource_name)
            dash_json = alert_utils.create_updated_dashboard(alert_dashboard,
                                                             alert_row)
            resp = dashboard._post_dashboard(dash_json)
            return resp
        else:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': "Dashboard not found"})

    def _delete_panel(self, cluster_id, resource_type, resource_name=None):
        alert_dashboard = alert_utils.get_alert_dashboard(resource_type)
        alert_utils.remove_row(alert_dashboard, cluster_id, resource_type, resource_name)
        resp = dashboard._post_dashboard(alert_dashboard)
        response = []
        response.append(copy.deepcopy(resp))
        if resource_name is None:
            dashboard_names = ["volumes", "hosts", "bricks"]
            for dash_name in dashboard_names:
                alert_dashboard = alert_utils.remove_cluster_rows(cluster_id,
                                                                  dash_name)
                resp = dashboard._post_dashboard(alert_dashboard)
                response.append(copy.deepcopy(resp))
        return response

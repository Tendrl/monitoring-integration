import json
import copy


from tendrl.monitoring_integration.flows.update_dashboard.alert_utils import get_alert_dashboard
from tendrl.monitoring_integration.flows.update_dashboard import alert_utils
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.commons import flows


class UpdateDashboard(flows.BaseFlow):

    def __init__(self):
        pass

    def run(self):
        super(UpdateDashboard, self).run()
        resource_name = str(self.parameters.get("Trigger.resource_name")).lower()
        resource_type = str(self.parameters.get("Trigger.resource_type")).lower()
        operation = str(self.parameters.get("Trigger.action")).lower()
        cluster_id = self.parameters.get("TendrlContext.integration_id")
        if operation.lower() == "add":
            self._add_panels(cluster_id, resource_type, resource_name)
        elif operation.lower() == "delete":
            self._delete_panel(cluster_id, resource_type, resource_name=None)

    def _add_panel(self, cluster_id, resource_type, resource_name=None):

        if resource_type == "volume":

            alert_dashboard = alert_utils.get_alert_dashboard("volumes")
            alert_row = alert_utils.fetch_row(alert_dashboard)
            alert_utils.add_volume_panel(alert_row, cluster_id, resource_name)
            dash_json = alert_utils.create_updated_dashboard(alert_dashboard,
                                                             alert_row)
            resp = dashboard._post_dashboard(json.dumps(dash_json))
            return resp

        elif resource_type == "host":

            alert_dashboard = alert_utils.get_alert_dashboard("hosts")
            alert_row = alert_utils.fetch_row(alert_dashboard)
            alert_utils.add_node_panel(alert_row, cluster_id, resource_name)
            dash_json = alert_utils.create_updated_dashboard(alert_dashboard,
                                                             alert_row)
            resp = dashboard._post_dashboard(json.dumps(dash_json))
            return resp

        elif resource_type == "brick":

            alert_dashboard = alert_utils.get_alert_dashboard("bricks")
            alert_row = alert_utils.fetch_row(alert_dashboard)
            alert_utils.add_brick_panel(alert_row, cluster_id, resource_name)
            dash_json = alert_utils.create_updated_dashboard(alert_dashboard,
                                                             alert_row)
            resp = dashboard._post_dashboard(json.dumps(dash_json))
            return resp

        elif resource_type == "cluster":

            alert_dashboard = alert_utils.get_alert_dashboard("at-a-glance")
            alert_row = alert_utils.fetch_row(alert_dashboard)
            alert_utils.add_cluster_panel(alert_row, cluster_id)
            dash_json = alert_utils.create_updated_dashboard(alert_dashboard,
                                                             alert_row)
            resp = dashboard._post_dashboard(json.dumps(dash_json))
            return resp

    def _delete_panel(self, cluster_id, resource_type, resource_name=None):

        if resource_name is None:
            resource_type = "at-a-glance"
        alert_dashboard = alert_utils.get_alert_dashboard(resource_type)
        alert_utils.remove_row(alert_dashboard, cluster_id, resource_name)
        resp = dashboard._post_dashboard(json.dumps(alert_dashboard))
        response = []
        response.append(copy.deepcopy(resp))
        if resource_name is None:
            dashboard_names = ["volumes", "hosts", "bricks"]
            for dash_name in dashboard_names:
                alert_dashboard = alert_utils.remove_cluster_rows(cluster_id,
                                                                  dash_name)
                resp = dashboard._post_dashboard(json.dumps(alert_dashboard))
                response.append(copy.deepcopy(resp))
        return response

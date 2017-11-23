import json
import copy
import etcd
import time


from tendrl.monitoring_integration.grafana.grafana_org_utils import  \
    get_current_org_name
from tendrl.monitoring_integration.grafana import create_alert_dashboard
from tendrl.monitoring_integration.flows.update_dashboard.alert_utils import \
    get_alert_dashboard
from tendrl.monitoring_integration.flows.update_dashboard import alert_utils
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.grafana import create_dashboards
from tendrl.commons import flows
from tendrl.commons.utils import etcd_utils
from tendrl.commons.utils import log_utils as logger


class UpdateDashboard(flows.BaseFlow):

    def run(self):
        super(UpdateDashboard, self).run()
        self.map = {"cluster": "at-a-glance", "host": "nodes",
                    "volume": "volumes", "brick": "bricks"}
        resource_name = self.parameters.get("Trigger.resource_name", None)
        if resource_name:
            resource_name = str(resource_name).lower()
        resource_type = str(
            self.parameters.get("Trigger.resource_type")).lower()
        operation = str(self.parameters.get("Trigger.action")).lower()
        integration_id = self.parameters.get("TendrlContext.integration_id")
        if operation.lower() == "delete":
            self._delete_panel(
                integration_id, self.map[resource_type], resource_name)
        else:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': "Wrong action"})

    def _add_panel(self, integration_id, resource_type, resource_name=None):
        if resource_type == "nodes":
            resource_name = resource_name.replace(".", "_")
        alert_dashboard = alert_utils.get_alert_dashboard(resource_type)
        if alert_dashboard:
            try:
                if alert_dashboard["message"] == "Dashboard not found":
                    flag = False
                else:
                    flag = True
            except (KeyError, AttributeError):
                    flag = True
            if flag:
                try:
                    # check duplicate rows
                    if not alert_utils.check_duplicate(
                        alert_dashboard,
                        integration_id,
                        resource_type,
                        resource_name
                    ):
                        alert_row = alert_utils.fetch_row(alert_dashboard)
                        alert_utils.add_resource_panel(
                        alert_row, integration_id, resource_type, resource_name)
                        dash_json = alert_utils.create_updated_dashboard(
                            alert_dashboard, alert_row)
                        self._post_dashboard(dash_json)
                except Exception:
                    logger.log("error", NS.get("publisher_id", None),
                               {'message': "Error while updating "
                                           "dashboard for %s" % resource_name})


    def _delete_panel(self, integration_id, resource_type, resource_name=None):
        if resource_type == "nodes":
            resource_name = resource_name.replace(".", "_")
        alert_dashboard = alert_utils.get_alert_dashboard(resource_type)
        alert_utils.remove_row(alert_dashboard,
                               integration_id,
                               resource_type,
                               resource_name)
        resp = self._post_dashboard(alert_dashboard)
        response = []
        response.append(copy.deepcopy(resp))
        if resource_name is None:
            dashboard_names = ["volumes", "hosts", "bricks"]
            for dash_name in dashboard_names:
                alert_dashboard = alert_utils.remove_cluster_rows(integration_id,
                                                                  dash_name)
                resp = self._post_dashboard(alert_dashboard)
                response.append(copy.deepcopy(resp))
        return response

    def _post_dashboard(self, alert_dashboard):
        resp = None
        if get_current_org_name()["name"] == "Alert_dashboard":
            resp = dashboard._post_dashboard(alert_dashboard)
        elif alert_utils.switch_context("Alert_dashboard"):
            resp = dashboard._post_dashboard(alert_dashboard)
            # return to main org
            alert_utils.switch_context("Main Org.")
        return resp

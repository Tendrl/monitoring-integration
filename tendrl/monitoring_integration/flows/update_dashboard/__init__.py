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
        if operation.lower() == "add":
            self._add_panel(
                integration_id, self.map[resource_type], resource_name)
        elif operation.lower() == "delete":
            self._delete_panel(
                integration_id, self.map[resource_type], resource_name)
        else:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': "Wrong action"})

    def _add_panel(self, integration_id, resource_type, resource_name=None,
                   recursive_call=False):
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
                    if len(alert_dashboard["dashboard"]["rows"]) == 0 or \
                        len(alert_dashboard["dashboard"]["rows"][0]["panels"]) == 0:
                        alert_utils.delete_alert_dashboard(resource_type)
                        self.create_all_dashboard(resource_type, integration_id)
                        if recursive_call:
                            return 1
                    else:
                        alert_row = alert_utils.fetch_row(alert_dashboard)
                        alert_utils.add_resource_panel(
                        alert_row, integration_id, resource_type, resource_name)
                        dash_json = alert_utils.create_updated_dashboard(
                            alert_dashboard, alert_row)
                        self._post_dashboard(dash_json)
                except Exception:
                    alert_utils.delete_alert_dashboard(resource_type)
                    self.create_all_dashboard(resource_type, integration_id)
                    if recursive_call:
                        return 1
            else:
                self.create_all_dashboard(resource_type, integration_id)
                if recursive_call:
                    return 1

        if resource_type is not "volumes":
            return 0
        else:
            cluster_key = "/clusters/" + str(integration_id)
            vol_id = None
            try_count = 0
            while try_count < 18 and not vol_id:
                time.sleep(10)
                if vol_id is not None:
                    break
                volumes = etcd_utils.read(cluster_key + "/Volumes")
                for volume in volumes.leaves:
                    volume_id = volume.key.rsplit("/")[-1]
                    try:
                        vol_name_key = cluster_key + "/Volumes/" + \
                            volume_id + "/name"
                        vol_name = etcd_utils.read(vol_name_key).value
                        if vol_name == resource_name:
                            vol_id = volume_id
                            break
                    except (etcd.EtcdKeyNotFound, KeyError):
                        try_count = try_count + 1
                        pass
            if try_count == 18:
                return 0

            time.sleep(10)
            volume_key = "/clusters/" + str(integration_id) + "/Volumes/" + \
                str(vol_id)
            subvols = etcd_utils.read(volume_key + "/Bricks")
            brick_list = []
            for subvol in subvols.leaves:
                subvol_name = subvol.key.rsplit("/")[-1]
                try:
                    subvolume_key = volume_key + "/Bricks/" + subvol_name
                    brick_details = etcd_utils.read(subvolume_key)
                    for entry in brick_details.leaves:
                        try:
                            brick_name = entry.key.rsplit("/", 1)[1]
                            brick_key = cluster_key + "/Bricks/all/" + \
                                brick_name.split(":", 1)[0] + \
                                "/" + brick_name.split(":_", 1)[1] + \
                                "/brick_path"
                            brick_name = etcd_utils.read(brick_key).value
                            brick_list.append(copy.deepcopy(brick_name))
                        except(KeyError, etcd.EtcdKeyNotFound):
                            pass
                except (KeyError, etcd.EtcdKeyNotFound):
                    pass
            for brick in brick_list:
                brick = resource_name + "|" + brick
                return_value = self._add_panel(integration_id, "bricks", brick, recursive_call=True)
                if return_value == 1:
                    return 0

    def create_all_dashboard(self, dashboard_name, integration_id):
        cluster_detail_list = []
        time.sleep(60)
        try:
            cluster_detail_list = create_dashboards.get_cluster_details(
                integration_id)
        except etcd.EtcdKeyNotFound:
            logger.log("error", NS.get("publisher_id", None),
                           {'message': "Failed to get cluster "
                            "details".format(integration_id)})
            return
        try:
            create_alert_dashboard.CreateAlertDashboard(dashboard_name, cluster_detail_list)
        except (etcd.EtcdKeyNotFound, KeyError) as error:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': "Failed to create dashboard"
                           "with error {0}".format(str(error))})

    def _delete_panel(self, integration_id, resource_type, resource_name=None):
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

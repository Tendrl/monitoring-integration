import json
import copy
import etcd
import time


from tendrl.monitoring_integration.flows.update_dashboard.alert_utils import get_alert_dashboard
from tendrl.monitoring_integration.flows.update_dashboard import alert_utils
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.grafana import create_dashboards
from tendrl.commons import flows
from tendrl.commons.utils import etcd_utils
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
            dash_json = alert_utils.create_updated_dashboard(alert_dashboard, alert_row)
            resp = dashboard._post_dashboard(dash_json)
        else:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': "Dashboard not found"})

        if resource_type == "volumes":
            cluster_key = "/clusters/" + str(cluster_id)
            volume_list = create_dashboards.get_resource_keys(cluster_key, "Volumes")
            vol_id = None
            try_count = 0
            while try_count < 18 and not vol_id:
                time.sleep(10)
                if vol_id is not None:
                    break
                for volume_id in volume_list:
                    try:
                        vol_name_key = cluster_key + "/" + volume_id + "/name"
                        vol_name = etcd_utils.read(vol_name_key).value
                        if vol_name == resource_name:
                            vol_id = volume_id
                            break
                    except (etcd.EtcdKeyNotFound, KeyError) as ex:
                        try_count = try_count + 1
                        pass
            if try_count == 18:
                return
            try_count = 0
            while try_count < 18:
                time.sleep(10)
                brick_list = []
                volume_key = "/clusters/" + str(cluster_id) + "/Volumes/" + str(vol_id)
                subvolume_list = create_dashboards.get_resource_keys(volume_key, "Bricks")
                for subvolume in subvolume_list:
                    try:
                        subvolume_key = volume_key + "/Bricks/" + subvolume
                        brick_details = etcd_utils.read(subvolume_key)
                        for entry in brick_details.leaves:
                            try:
                                brick_name = entry.key.rsplit("/", 1)[1]
                                brick_key = cluster_key + "/Bricks/all/" + brick_name.split(":", 1)[0] + \
                                     "/" + brick_name.split(":_", 1)[1] + "/" + brick_path
                                brick_name = etcd_utils.read(brick_key).value
                                brick_list.append(copy.deepcopy(brick_name))
                            except(KeyError, etcd.EtcdKeyNotFound) as ex:
                                pass
                    except (KeyError, etcd.EtcdKeyNotFound) as ex:
                        try_count = try_count + 1
                        pass
            if try_count == 18:
                return
            for brick in brick_list:
                self._add_panel(cluster_id, "bricks", brick)

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

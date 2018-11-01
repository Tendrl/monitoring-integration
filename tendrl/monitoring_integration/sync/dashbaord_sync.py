import copy
import etcd
from requests import exceptions as req_excep

from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import alert_dashboard
from tendrl.monitoring_integration.grafana import \
    alert_organization
from tendrl.monitoring_integration.grafana import alert_utils
from tendrl.monitoring_integration.grafana import constants
from tendrl.monitoring_integration.grafana import exceptions


class SyncAlertDashboard(object):
    def refresh_dashboard(
        self, all_cluster_details
    ):
        cluster_details = {}
        try:
            # check alert organization is exist
            if NS.config.data["org_id"]:
                if len(all_cluster_details.keys()) > 0:
                    for integration_id in all_cluster_details:
                        cluster_details['hosts'] = []
                        cluster_details['volumes'] = []
                        cluster_details['bricks'] = []
                        node_details = self.get_node_details(
                            all_cluster_details[integration_id]["hosts"],
                            integration_id
                        )
                        cluster_details['hosts'].extend(
                            node_details
                        )
                        volume_details = self.get_volume_details(
                            all_cluster_details[integration_id]["volumes"],
                            integration_id
                        )
                        cluster_details['volumes'].extend(
                            volume_details
                        )
                        brick_details = self.get_brick_details(
                            all_cluster_details[integration_id]["bricks"],
                            integration_id
                        )
                        cluster_details['bricks'].extend(
                            brick_details
                        )
                    self.create_alert_dashboard(
                        cluster_details
                    )
                else:
                    # no cluster is managed
                    # delete all dashbaords
                    dashboards = constants.GLUSTER_DASHBOARDS
                    # In future append other dashbaords also
                    for dashboard in dashboards:
                        alert_utils.delete_alert_dashboard(dashboard)
            else:
                # try to create alert organization once again
                alert_organization.create()
        except (etcd.EtcdException,
                KeyError,
                AttributeError,
                req_excep.ConnectionError,
                TypeError,
                req_excep.RequestException,
                exceptions.ConnectionFailedException,
                exceptions.AlertOrganizationNotFound) as ex:
            logger.log("debug", NS.get("publisher_id", None),
                       {'message': "Failed to update cluster "
                       "dashboard.err: %s" % str(ex)})

    def create_alert_dashboard(
        self, cluster_details
    ):
        for dashboard_name in cluster_details:
            no_changes_in_dashboard = False
            # check alert dashboard exist
            resource_json = alert_utils.get_alert_dashboard(
                dashboard_name
            )
            dashboard_found = True
            if "message" in resource_json and \
                    "Dashboard not found" in resource_json["message"]:
                dashboard_found = False
            if dashboard_found:
                try:
                    rows_len = len(
                        resource_json["dashboard"]["rows"]
                    )
                    panels_len = 0
                    if rows_len > 0 and "panels" in resource_json[
                            "dashboard"]["rows"][0]:
                        panels_len = len(
                            resource_json["dashboard"][
                                "rows"][0]["panels"]
                        )
                    if rows_len == 0 or panels_len == 0:
                        alert_utils.delete_alert_dashboard(dashboard_name)
                        if cluster_details[dashboard_name]:
                            resource_json = self.create_dashboard(
                                dashboard_name,
                                cluster_details[dashboard_name]
                            )
                    else:
                        resource_json, no_changes_in_dashboard = \
                            self.update_dashboard(
                                dashboard_name,
                                cluster_details[dashboard_name],
                                resource_json
                            )
                except (KeyError, AttributeError) as ex:
                    logger.log(
                        "error",
                        NS.publisher_id,
                        {
                            "message": "Failed to update alert "
                            "dashboard %s err: %s" % (dashboard_name, ex)
                        }
                    )
                    raise ex
            else:
                if len(cluster_details[dashboard_name]) > 0:
                    resource_json = self.create_dashboard(
                        dashboard_name,
                        cluster_details[dashboard_name]
                    )
                else:
                    # no detail present then no need to create
                    # alert dashboard
                    continue
            if resource_json and not no_changes_in_dashboard:
                resp = alert_utils.post_dashboard(resource_json)
                self.log_message(resp, dashboard_name)

    def create_dashboard(self, resource_type, resources):
        resource_json = {}
        # create dashboard
        if resources:
            # Create operation takes more excution time than update
            # Create dashboard for one resource using that do update for
            # other resources
            resource = resources.pop()
            resource_json = alert_dashboard.create_resource_dashboard(
                resource_type,
                resource
            )
        # After creating first panel update the other panels
        if resources and resource_json:
            # update dashboard
            rows = resource_json["dashboard"]["rows"]
            most_recent_panel_id = rows[-1]["panels"][-1]["id"]
            resource_json = alert_dashboard.add_panel(
                resources,
                resource_type,
                resource_json,
                most_recent_panel_id
            )
        return resource_json

    def update_dashboard(self, resource_type, resources, resource_json):
        no_changes_in_dashboard = False
        new_resources, alert_dashboard_json, most_recent_panel_id = \
            alert_dashboard.check_duplicate(
                copy.deepcopy(resource_json),
                resources,
                resource_type
            )
        if new_resources and len(
            alert_dashboard_json["dashboard"]["rows"]
        ) > 0:
            alert_dashboard_json = alert_dashboard.add_panel(
                new_resources,
                resource_type,
                alert_dashboard_json,
                most_recent_panel_id
            )
        elif len(resource_json["dashboard"]["rows"]) == \
                len(alert_dashboard_json["dashboard"]["rows"]):
            no_changes_in_dashboard = True
        return alert_dashboard_json, no_changes_in_dashboard

    def get_node_details(self, nodes, integration_id):
        node_details = []
        for node in nodes:
            node_detail = (
                {"fqdn": node.fqdn,
                 "integration_id": integration_id,
                 "resource_name": str(node.fqdn).replace(".", "_"),
                 "sds_name": constants.GLUSTER
                 }
            )
            node_details.append(node_detail)
        return node_details

    def get_volume_details(
        self, volumes, integration_id
    ):
        volume_details = []
        for volume in volumes:
            volume_detail = (
                {"name": volume.name,
                 "vol_id": volume.vol_id,
                 "integration_id": integration_id,
                 "resource_name": str(volume.name),
                 "sds_name": constants.GLUSTER
                 }
            )
            volume_details.append(volume_detail)
        return volume_details

    def get_brick_details(self, bricks, integration_id):
        brick_details = []
        for brick in bricks:
            brick_detail = (
                {"hostname": brick.fqdn,
                 "vol_id": brick.vol_id,
                 "vol_name": brick.vol_name,
                 "brick_path": brick.brick_path.split(
                     ":")[1].replace("/", "|"),
                 "integration_id": integration_id,
                 "sds_name": constants.GLUSTER,
                 "resource_name": "%s|%s:%s" % (
                     str(brick.vol_name),
                     brick.fqdn,
                     brick.brick_path.split(":")[1].replace("/", "|")
                 )
                 }
            )
            brick_details.append(brick_detail)
        return brick_details

    def log_message(self, response, resource_type):
        try:
            if response.status_code == 200:
                msg = "{0} dashboard uploaded successfully".format(
                    resource_type
                )
            else:
                msg = "{0} dashboard upload failed".format(
                    resource_type
                )

            logger.log("debug", NS.get("publisher_id", None),
                       {'message': msg})
        except (KeyError, AttributeError):
            pass

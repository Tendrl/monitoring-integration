import etcd
from requests import exceptions as req_excep

from tendrl.commons.utils import etcd_utils
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import alert_utils
from tendrl.monitoring_integration.grafana import constants
from tendrl.monitoring_integration.grafana import create_alert_dashboard
from tendrl.monitoring_integration.grafana import \
    create_alert_organization
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration.sync import gluster_cluster_details


class SyncAlertDashboard(object):
    def refresh_dashboard(self):
        try:
            # check alert organization is exist
            if NS.config.data["org_id"]:
                cluster_details = {}
                dashboards = []
                integration_ids = utils.get_resource_keys("", "clusters")
                for integration_id in integration_ids:
                    key = "/clusters/%s/TendrlContext/sds_name" % \
                        integration_id
                    sds_name = etcd_utils.read(key).value
                    if sds_name == constants.GLUSTER:
                        cluster_details, dashboards = gluster_cluster_details.\
                            get_cluster_details(
                                integration_id
                            )
                        cluster_details["sds_name"] = constants.GLUSTER
                    self.update_dashboard(cluster_details, dashboards)
            else:
                # try to create alert organization once again
                create_alert_organization.create()
        except (etcd.EtcdException,
                KeyError,
                AttributeError,
                req_excep.ConnectionError,
                TypeError,
                req_excep.RequestException,
                exceptions.ConnectionFailedException,
                exceptions.AlertOrganizationNotFound) as ex:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': "Failed to update cluster "
                       "dashboard.err: %s" % str(ex)})

    def update_dashboard(self, cluster_details, dashboards):
        for dashboard_name in dashboards:
            if dashboard_name in cluster_details and \
                    cluster_details[dashboard_name]:
                # check alert dashboard exist
                alert_dashboard = alert_utils.get_alert_dashboard(
                    dashboard_name
                )
                flag = True
                if "message" in alert_dashboard and \
                        alert_dashboard["message"] == "Dashboard not found":
                    flag = False
                if flag:
                    try:
                        rows_len = len(
                            alert_dashboard["dashboard"]["rows"]
                        )
                        if rows_len > 0 and "panels" in alert_dashboard[
                                "dashboard"]["rows"][0]:
                            panels_len = len(
                                alert_dashboard["dashboard"][
                                    "rows"][0]["panels"]
                            )
                        else:
                            panels_len = 0
                        if rows_len == 0 or panels_len == 0:
                            alert_utils.delete_alert_dashboard(dashboard_name)
                            self.create_dashboard(
                                dashboard_name,
                                cluster_details
                            )
                        else:
                            if cluster_details["sds_name"] == \
                                    constants.GLUSTER:
                                self.create_gluster_resource(
                                    cluster_details[dashboard_name],
                                    dashboard_name,
                                    cluster_details["integration_id"],
                                    cluster_details["sds_name"]
                                )
                    except (KeyError, AttributeError):
                        alert_utils.delete_alert_dashboard(dashboard_name)
                        self.create_dashboard(
                            dashboard_name,
                            cluster_details
                        )

                else:
                    self.create_dashboard(
                        dashboard_name,
                        cluster_details
                    )

    def create_dashboard(self, resource_name, cluster_details):
        flag = False
        for resource in cluster_details[resource_name]:
            if not flag:
                # create dashboard
                create_alert_dashboard.create_resource_dashboard(
                    resource_name,
                    resource,
                    cluster_details["sds_name"],
                    cluster_details["integration_id"]
                )
                flag = True
            else:
                # update dashboard
                self.create_gluster_resource(
                    resource,
                    resource_name,
                    cluster_details["integration_id"],
                    cluster_details["sds_name"]
                )

    def create_gluster_resource(self, resource, resource_type,
                                integration_id, sds_name):
        if resource_type == "volumes":
            for volume in resource:
                try:
                    resource_name = str(volume["name"])
                    response = create_alert_dashboard.add_panel(
                        integration_id,
                        resource_type,
                        resource_name,
                        sds_name
                    )
                    if response:
                        self.log_message(response, resource_name, "volume")
                except KeyError:
                    logger.log("error", NS.get("publisher_id", None),
                               {'message': "Failed to get volume {} "
                                "details".format(volume)})
        if resource_type == "hosts":
            for host in resource:
                try:
                    resource_name = str(host["fqdn"]).replace(".", "_")
                    response = create_alert_dashboard.add_panel(
                        integration_id,
                        resource_type,
                        resource_name,
                        sds_name
                    )
                    self.log_message(response, resource_name, "host")
                except KeyError:
                    logger.log("error", NS.get("publisher_id", None),
                               {'message': "Failed to get host {} "
                                "details".format(host)})

        if resource_type == "bricks":
            for brick in resource:
                try:
                    resource_name = "%s|%s:%s" % (
                        str(brick["vol_name"]),
                        brick["hostname"],
                        brick["brick_path"].replace("|", "/")
                    )
                    response = create_alert_dashboard.add_panel(
                        integration_id,
                        resource_type,
                        resource_name,
                        sds_name)
                    self.log_message(response, resource_name, "brick")
                except KeyError:
                    logger.log("error", NS.get("publisher_id", None),
                               {'message': "Failed to get brick {} "
                                "details".format(brick)})

    def log_message(self, response, resource_name, resource_type):
        try:
            if response.status_code == 200:
                msg = '\n' + "Dashboard for resource {0} uploaded " + \
                    "successfully for resource type {1}".format(resource_name,
                                                                resource_type)
            else:
                msg = '\n' + "Dashboard for resource {0} upload failed  " + \
                    "for resource type {1}".format(resource_name,
                                                   resource_type)

            logger.log("info", NS.get("publisher_id", None),
                       {'message': msg})
        except (KeyError, AttributeError):
            pass

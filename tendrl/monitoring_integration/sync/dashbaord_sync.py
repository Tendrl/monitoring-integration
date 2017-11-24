import time

import etcd


from tendrl.monitoring_integration.grafana import create_alert_dashboard
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.flows.update_dashboard import alert_utils
from tendrl.monitoring_integration.grafana import create_dashboards
from tendrl.monitoring_integration.flows.update_dashboard import \
    UpdateDashboard
from tendrl.monitoring_integration.grafana import create_dashboards
from tendrl.commons.utils import log_utils as logger


DASHBOARDS = ["volumes", "nodes", "bricks"]


class SyncDashboard():

    def refresh_dashboard(self):
        cluster_detail_list = []
        try:
            cluster_detail_list = create_dashboards.get_cluster_details()
        except etcd.EtcdKeyNotFound:
            logger.log("error", NS.get("publisher_id", None),
                           {'message': "Failed to get cluster "
                            "details"})
            return
        if cluster_detail_list:
            for dashboard_name in DASHBOARDS:
                alert_dashboard = alert_utils.get_alert_dashboard(dashboard_name)
                flag = False

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
                            alert_utils.delete_alert_dashboard(dashboard_name)
                            self.create_all_dashboard(dashboard_name, cluster_detail_list)
                        else:
                            self.create_resource(
                                cluster_detail_list, dashboard_name)
                    except (KeyError, AttributeError):
                        alert_utils.delete_alert_dashboard(dashboard_name)
                        self.create_all_dashboard(dashboard_name, cluster_detail_list)

                else:
                    self.create_all_dashboard(dashboard_name, cluster_detail_list)

    def create_all_dashboard(self, dashboard_name, cluster_detail_list):
        if dashboard_name == "nodes":
            dashboard_name = "hosts"
        try:
            create_alert_dashboard.CreateAlertDashboard(dashboard_name, cluster_detail_list)
        except (etcd.EtcdKeyNotFound, KeyError) as error:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': "Failed to create dashboard"
                           "with error {0}".format(str(error))})

    def create_resource(self, cluster_detail_list, resource_type):
        update_dashboard = UpdateDashboard()
        self.map = {"cluster": "at-a-glance", "host": "nodes",
                    "volume": "volumes", "brick": "bricks"}
        for cluster in cluster_detail_list:
            integration_id = cluster.integration_id
            if resource_type == "volumes":
                for volume in cluster.volumes:
                    time.sleep(3)
                    try:
                        resource_name = str(volume["name"])
                        response = update_dashboard._add_panel(
                           integration_id,
                           self.map["volume"],
                           resource_name)
                        self.log_message(response, resource_name, "volume")
                    except KeyError:
                        logger.log("error", NS.get("publisher_id", None),
                                   {'message': "Failed to get volume {} "
                                      "details".format(volume)})
            if resource_type == "nodes":
                for host in cluster.hosts:
                    time.sleep(3)
                    try:
                        resource_name = str(host["fqdn"])
                        response = update_dashboard._add_panel(
                            integration_id,
                            self.map["host"],
                            resource_name)
                        self.log_message(response, resource_name, "host")
                    except KeyError:
                        logger.log("error", NS.get("publisher_id", None),
                                   {'message': "Failed to get host {} "
                                       "details".format(host)})

            if resource_type == "bricks":
                for brick in cluster.bricks:
                    time.sleep(3)
                    try:
                        resource_name = "%s|%s:%s" % (
                            str(brick["vol_name"]),
                            brick["hostname"],
                            brick["brick_path"].replace("|", "/")
                        )
                        response = update_dashboard._add_panel(
                            integration_id,
                            self.map["brick"],
                            resource_name)
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

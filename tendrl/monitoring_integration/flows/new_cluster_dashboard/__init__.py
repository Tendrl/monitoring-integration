import etcd


from tendrl.commons import flows
from tendrl.monitoring_integration.grafana import create_alert_dashboard
from tendrl.monitoring_integration.flows.update_dashboard import alert_utils
from tendrl.monitoring_integration.flows.update_dashboard import UpdateDashboard
from tendrl.monitoring_integration.grafana import create_dashboards
from tendrl.commons.utils import log_utils as logger


class NewClusterDashboard(flows.BaseFlow):

    def run(self):
        super(NewClusterDashboard, self).run()
        cluster_id = self.parameters.get("TendrlContext.integration_id")
        self.upload_alert_dashboard(cluster_id)

    def upload_alert_dashboard(self, integration_id=None):
        super(NewClusterDashboard, self).run()
        if not integration_id:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': "cluster id not found"})
            return
        self.map = {"cluster" : "at-a-glance", "host": "nodes", "volume" : "volumes", "brick" : "bricks"}
        alert_host_dashboard = alert_utils.get_alert_dashboard("nodes")
        flag = False
        if alert_host_dashboard:
            try:
                if alert_host_dashboard["message"] == "Dashboard not found":
                    flag = False
                else:
                    flag = True
            except Exception as ex:
                flag = True
        update_dashboard = UpdateDashboard()
        if flag:
            try:
                cluster_detail_list = create_dashboards.get_cluster_details(integration_id)
                for cluster in cluster_detail_list:
                    for brick in cluster.bricks:
                        try:
                            resource_name = brick["vol_name"] + "|" + brick["hostname"] + ":" + brick["brick_path"].replace("|", "/")
                            response = update_dashboard._add_panel(integration_id, self.map["brick"], resource_name)
                            self.log_message(response, resource_name, "brick")
                        except KeyError as ex:
                            logger.log("error", NS.get("publisher_id", None),
                                       {'message': "Failed to get brick {} details".format(brick)})
                    for volume in cluster.volumes:
                        try:
                            resource_name = str(volume["name"])
                            response = update_dashboard._add_panel(integration_id, self.map["volume"], resource_name)
                            self.log_message(response, resource_name, "volume")
                        except KeyError as ex:
                            logger.log("error", NS.get("publisher_id", None),
                                       {'message': "Failed to get volume {} details".format(volume)})
                    for host in cluster.hosts:
                        try:
                            resource_name = str(host["fqdn"])
                            response = update_dashboard._add_panel(integration_id, self.map["host"], resource_name)
                            self.log_message(response, resource_name, "host")
                        except KeyError as ex:
                            logger.log("error", NS.get("publisher_id", None),
                                       {'message': "Failed to get host {} details".format(host)})
            except etcd.EtcdKeyNotFound as ex:
                logger.log("error", NS.get("publisher_id", None),
                           {'message': "Failed to get cluster details".format(integration_id)})

        else:
            try:
                alert_dash_obj = create_alert_dashboard.CreateAlertDashboard()
            except (etcd.EtcdKeyNotFound, KeyError) as ex:
                logger.log("error", NS.get("publisher_id", None),
                           {'message': "Failed to get host {} details".format(host)})

    def log_message(self, response, resource_name, resource_type):
        try:
            if response.status_code == 200:
                msg = '\n' + "Dashboard for resource {0} uploaded successfully for resource type {1}".format(resource_name, resource_type)
            else:
                msg = '\n' + "Dashboard for resource {0} upload failed  for resource type {1}".format(resource_name, resource_type)

            logger.log("info", NS.get("publisher_id", None),
                       {'message': msg})
        except (KeyError, AttributeError) as ex:
            pass
             

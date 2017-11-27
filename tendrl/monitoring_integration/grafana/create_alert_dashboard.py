import json
import time

import etcd


from tendrl.monitoring_integration.grafana import create_dashboards
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.grafana import grafana_org_utils
from tendrl.monitoring_integration.grafana import datasource
from tendrl.commons.utils import log_utils as logger
from tendrl.commons.utils import etcd_utils


class CreateAlertDashboard():

    def __init__(self, resource_type=None, cluster_detail_list=None):
        org_key = "_NS/monitoring/grafana_org_id"
        auth_key = "_NS/monitoring/grafana_auth_key"
        if not cluster_detail_list:
            cluster_detail_list = create_dashboards.get_cluster_details()
        org_id = NS.config.data.get("org_id", None)
        if not org_id:
            try:
                org_id = etcd_utils.read(org_key).value
            except etcd.EtcdKeyNotFound:
                org_id = grafana_org_utils.create_org("Alert_dashboard")
                try:
                    etcd_utils.write(org_key, org_id)
                except etcd.EtcdKeyNotFound:
                    pass
                NS.config.data["org_id"] = org_id
        key = ""
        if grafana_org_utils.switch_context(org_id):
            key = NS.config.data.get("grafana_auth_key", None)
            if not key:
                try:
                    key = etcd_utils.read(auth_key).value
                except etcd.EtcdKeyNotFound:
                    key = grafana_org_utils.create_api_token(
                        "grafana_auth_key", "Admin")
                    try:
                        etcd_utils.write(auth_key, key)
                    except etcd.EtcdKeyNotFound:
                        pass
                    NS.config.data["grafana_auth_key"] = key
            response = datasource.create_datasource()
            if response.status_code == 200:
                msg = '\n' + "Datasource " + \
                      " uploaded successfully" + '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})

            else:
                msg = "Datasource upload failed. Error code: {0} ," + \
                      "Error message: " + \
                      "{1} ".format(
                          response.status_code,
                          str(self.get_message_from_response(response)))
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})
            if cluster_detail_list:
                resource_name = []
                if not resource_type:
                    resource_name = ["volumes", "hosts", "bricks", "clusters"]
                else:
                    resource_name = [resource_type]
                for resource in resource_name:
                    # Uploading Alert Dashboards
                    resource_dashboard = \
                        create_dashboards.create_resource_dashboard(
                            cluster_detail_list, resource)
                    response = dashboard._post_dashboard(
                        resource_dashboard, key)
                    if response.status_code == 200:
                        msg = '\n' + "{} dashboard uploaded successfully". \
                            format(str(resource)) + '\n'
                        logger.log("info", NS.get("publisher_id", None),
                                   {'message': msg})
                    else:
                        msg = '\n' + "{} dashboard upload failed".format(
                            str(resource)) + '\n'
                        logger.log("info", NS.get("publisher_id", None),
                                   {'message': msg})
        else:
            msg = "Could not switch context, Alert dashboard upload failed"
            logger.log("error", NS.get("publisher_id", None),
                       {'message': msg})

    def get_message_from_response(self, response_data):

        message = ""
        try:
            if isinstance(json.loads(response_data.content), list):
                message = str(json.loads(response_data.content)[0]["message"])
            else:
                message = str(json.loads(response_data.content)["message"])
        except (AttributeError, KeyError):
            pass

        return message

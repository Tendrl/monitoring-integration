import json


from tendrl.monitoring_integration.grafana import create_dashboards
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.grafana import grafana_org_utils
from tendrl.monitoring_integration.grafana import datasource
from tendrl.commons.utils import log_utils as logger


class CreateAlertDashboard():

    def __init__(self):

        cluster_detail_list = create_dashboards.get_cluster_details()
        org_id  = grafana_org_utils.create_org("Alert_dashboard")
        key = ""
        if grafana_org_utils.switch_context(org_id):
            key = grafana_org_utils.create_api_token("Tendrl_auth_key", "Admin")
            response = datasource.create_datasource()
            if response.status_code == 200:
                msg = '\n' + "Datasource " + \
                      " uploaded successfully" + '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})

            else:
                msg = "Datasource upload failed. Error code: {0} ," + \
                      "Error message: " + \
                      "{1} ".format(response.status_code,
                                    str(self.get_message_from_response(response)))
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})
            if cluster_detail_list:
                resource_name = ["volumes", "hosts", "bricks", "clusters"]
                for resource in resource_name:
                    # Uploading Alert Dashboards
                    resource_dashboard = create_dashboards.create_resource_dashboard(cluster_detail_list, resource)
                    response = dashboard._post_dashboard(resource_dashboard, key)
                    if response.status_code == 200:
                        msg = '\n' + "{} dashboard uploaded successfully".format(str(resource)) + '\n'
                        logger.log("info", NS.get("publisher_id", None),
                                   {'message': msg})
                    else:
                        msg = '\n' + "{} dashboard upload failed".format(str(resource)) + '\n'
                        logger.log("info", NS.get("publisher_id", None),
                                   {'message': msg})
        else:
            msg = "Could not switch context, Alert dashboard upload failed"
            logger.log("error", NS.get("publisher_id", None),
                                   {'message': msg})

    def get_message_from_response(self, response_data):

        message = ""
        try :
            if isinstance(json.loads(response_data._content), list):
                message = str(json.loads(response._content)[0]["message"])
            else:
                message = str(json.loads(response_data._content)["message"])
        except (AttributeError, KeyError):
            pass

        return message

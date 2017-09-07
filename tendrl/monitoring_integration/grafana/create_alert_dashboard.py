from tendrl.monitoring_integration.grafana import create_dashboards
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.commons.utils import log_utils as logger


class CreateAlertDashboard():

    def __init__(self):

        cluster_detail_list = create_dashboards.get_cluster_details()

        if cluster_detail_list:
            resource_name = ["volumes", "hosts", "bricks", "clusters"]
            for resource in resource_name:
                # Uploading Alert Dashboards
                resource_dashboard = create_dashboards.create_resource_dashboard(cluster_detail_list, resource)
                response = dashboard._post_dashboard(resource_dashboard)
                if response.status_code == 200:
                    msg = '\n' + "{} dashboard uploaded successfully".format(str(resource)) + '\n'
                    logger.log("info", NS.get("publisher_id", None),
                               {'message': msg})
                else:
                    msg = '\n' + "{} dashboard upload failed".format(str(resource)) + '\n'
                    logger.log("info", NS.get("publisher_id", None),
                               {'message': msg})

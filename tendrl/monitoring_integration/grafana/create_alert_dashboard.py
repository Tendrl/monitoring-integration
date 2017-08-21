from tendrl.monitoring_integration.grafana import cluster_details
from tendrl.monitoring_integration.grafana import create_dashboards
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.commons.utils import log_utils as logger


class CreateAlertDashboard():

    def __init__(self):

        cluster_detail_list = create_dashboards.get_cluster_details()

        if cluster_detail_list:

            # Uploading Alert Dashboard for Volume
            volume_dashboard = create_dashboards.create_volume_dashboard(cluster_detail_list)
            response = dashboard._post_dashboard(volume_dashboard)
            if response.status_code == 200:

                msg = '\n' + "Volume Dashboard uploaded successfully" + '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})
            else:
                msg = '\n' + "Volume Dashboard uploaded failed" + '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})


            # Uploading Alert Dashboard for Brick
            brick_dashboard = create_dashboards.create_brick_dashboard(cluster_detail_list)
            response = dashboard._post_dashboard(brick_dashboard)
            if response.status_code == 200:

                msg = '\n' + "Brick Dashboard uploaded successfully" + '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})
            else:
                msg = '\n' + "Brick Dashboard uploaded failed" + '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})


            # Uploading Alert Dashboard for Host
            host_dashboard = create_dashboards.create_host_dashboard(cluster_detail_list)
            response = dashboard._post_dashboard(host_dashboard)
            if response.status_code == 200:

                msg = '\n' + "Host Dashboard uploaded successfully" + '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})
            else:
                msg = '\n' + "Host Dashboard uploaded failed" + '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})


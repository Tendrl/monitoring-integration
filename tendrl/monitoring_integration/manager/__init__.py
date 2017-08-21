import __builtin__
import traceback
import json


import signal
import maps
import gevent
import os


from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.grafana import datasource
from tendrl.monitoring_integration.grafana import create_new_notification_channel
from tendrl.commons import manager as common_manager
from tendrl.monitoring_integration.grafana.create_alert_dashboard import CreateAlertDashboard
from tendrl import monitoring_integration
from tendrl.monitoring_integration import sync
from tendrl.commons import TendrlNS
from tendrl.commons.utils import log_utils as logger


class MonitoringIntegrationManager(common_manager.Manager):

    def __init__(self):

        self._complete = gevent.event.Event()
        super(
            MonitoringIntegrationManager,
            self
        ).__init__(
            NS.sync_thread
        )

    def start(self):

        super(MonitoringIntegrationManager, self).start()
        _upload_default_dashboards()
        response = create_new_notification_channel.create_notification_channel()
        if response.status_code == 200:
            msg = "Notification created successfully"
            logger.log("info", NS.get("publisher_id", None),
                       {'message': msg})
        else:
            message = str(json.loads(response._content)["message"])
            logger.log("info", NS.get("publisher_id", None),
                       {'message': message})
        create_alert_dashboard = CreateAlertDashboard()




def _upload_default_dashboards():

        monitoring_integration_manager = MonitoringIntegrationManager()

        # Creating Default Dashboards
        dashboards = []
        utils.get_conf()
        dashboards = dashboard.get_all_dashboards()

        title = []

        for dashboard_json in dashboards:
            title.append(dashboard_json["uri"].split('/')[1])

        for dashboard_json in NS.config.data["dashboards"]:
            if dashboard_json in title:
                msg = '\n' + "Dashboard " + str(dashboard_json) + \
                      " already exists" + '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})
                continue
            response = dashboard.create_dashboard(dashboard_json)

            if response.status_code == 200:
                msg = '\n' + "Dashboard " + str(dashboard_json)+ \
                      " uploaded successfully" + '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})
            else:
                msg = '\n' + "Dashboard " + str(dashboard_json) + \
                   " upload failed with error code " + str(response.status_code) + \
                   '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})
        try:
            dashboard_json = dashboard.get_dashboard(NS.config.data["home_dashboard"])

            if 'dashboard' in dashboard_json:
                dashboard_id = dashboard_json.get('dashboard').get('id')
                response = dashboard.set_home_dashboard(dashboard_id)

                response = dashboard.set_home_dashboard(dashboard_id)
                if response.status_code == 200:
                    msg = '\n' + "Dashboard " + \
                          str(NS.config.data["home_dashboard"]) + \
                          " is set as home dashboard" + '\n'
                    logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})
            else:
                msg = '\n' + str(dashboard_json.get('message')) + '\n'
                logger.log("info", NS.get("publisher_id", None),
                           {'message': msg})
        except exceptions.ConnectionFailedException:
            traceback.print_exc()
            raise exceptions.ConnectionFailedException

        # Creating datasource
        response = datasource.create_datasource()
        if response.status_code == 200:
            msg = '\n' + "Datasource " + \
                  " uploaded successfully" + '\n'
            logger.log("info", NS.get("publisher_id", None),
                       {'message': msg})

        else:
            if isinstance(json.loads(response._content), list):
                message = str(json.loads(response._content)[0]["message"])
            else:
                message = str(json.loads(response._content)["message"])
            msg = '\n' + "Datasource " + " upload failed with" + '\n' + "Message \"" + \
                  message + "\"" + \
                  " and Error code " + str(response.status_code) + '\n'
            logger.log("info", NS.get("publisher_id", None),
                       {'message': msg})


def main():

    monitoring_integration.MonitoringIntegrationNS()

    TendrlNS()
    NS.type = "monitoring"
    NS.publisher_id = "monitoring_integration"
    NS.monitoring.config.save()
    NS.monitoring.definitions.save()
    NS.sync_thread = sync.MonitoringIntegrationSdsSyncThread()

    monitoring_integration_manager = MonitoringIntegrationManager()
    monitoring_integration_manager.start()
    complete = gevent.event.Event()
  
    def shutdown():
        complete.set()

    gevent.signal(signal.SIGTERM, shutdown)
    gevent.signal(signal.SIGINT, shutdown)

    while not complete.is_set():
        complete.wait(timeout=1)


if __name__ == '__main__':
    main()

import __builtin__
import json
import os
import signal
import threading
import time
import traceback

import maps


from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.grafana import create_alert_dashboard
from tendrl.monitoring_integration.grafana import datasource

from tendrl.monitoring_integration.grafana import webhook_receiver
from tendrl.monitoring_integration.grafana import \
    create_new_notification_channel
from tendrl.commons import manager as common_manager
from tendrl import monitoring_integration
from tendrl.monitoring_integration import sync
from tendrl.commons import TendrlNS
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import grafana_org_utils


class MonitoringIntegrationManager(common_manager.Manager):

    def __init__(self):

        self._complete = threading.Event()
        super(
            MonitoringIntegrationManager,
            self
        ).__init__(
            NS.sync_thread
        )
        self.webhook_receiver = webhook_receiver.WebhookReceiver()

    def start(self):

        super(MonitoringIntegrationManager, self).start()
        # Creating Default Dashboards
        _upload_default_dashboards()
        create_alert_dashboard.CreateAlertDashboard()
        create_new_notification_channel.create_notification_channel(
            "tendrl_notification_channel",
            NS.config.data["grafana_host"],
            8789
        )
        self.webhook_receiver.start()


def _upload_default_dashboards():
    dashboards = []
    utils.get_conf()
    dashboards = dashboard.get_all_dashboards()
    try:
        main_org_id = grafana_org_utils.get_org_id("Main Org.")
        if main_org_id:
            response = grafana_org_utils.switch_context(json.loads(main_org_id)["id"])
    except (exceptions.ConnectionFailedException, KeyError) as ex:
        msg = (json.loads(main_org_id)).get("message", "Cannot connect to grafana")
        logger.log("error", NS.get("publisher_id", None),
                       {'message': msg})
        raise ex
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
            msg = '\n' + "Dashboard " + str(dashboard_json) + \
                  " uploaded successfully" + '\n'
            logger.log("info", NS.get("publisher_id", None),
                       {'message': msg})
        else:
            msg = "Dashboard {0} upload failed. Error code: {1} ," + \
                  "Error message: " + \
                  "{2} ".format(str(dashboard_json),
                                str(response.status_code),
                                str(get_message_from_response(response)))
            logger.log("info", NS.get("publisher_id", None),
                       {'message': msg})
    try:
        dashboard_json = dashboard.get_dashboard(
            NS.config.data["home_dashboard"])

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
    except exceptions.ConnectionFailedException as ex:
        traceback.print_exc()
        logger.log("error", NS.get("publisher_id", None),
                   {'message': str(ex)})
        raise exceptions.ConnectionFailedException

    # Creating datasource
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
                            str(get_message_from_response(response)))
        logger.log("info", NS.get("publisher_id", None),
                   {'message': msg})


def get_message_from_response(response_data):

    message = ""
    try:
        if isinstance(json.loads(response_data.content), list):
            message = str(json.loads(response_data.content)[0]["message"])
        else:
            message = str(json.loads(response_data.content)["message"])
    except (AttributeError, KeyError):
        pass

    return message


def main():

    monitoring_integration.MonitoringIntegrationNS()

    TendrlNS()
    grafana_conn_count = 0
    while grafana_conn_count < 10:
        if not utils.port_open(3000, "127.0.0.1"):
            grafana_conn_count = grafana_conn_count + 1
            time.sleep(4)
        else:
            break
    if grafana_conn_count == 10:
        logger.log("info", NS.get("publisher_id", None),
                   {'message': "Cannot connect to Grafana"})
        return
    NS.type = "monitoring"
    NS.publisher_id = "monitoring_integration"
    if NS.config.data.get("with_internal_profiling", False):
        from tendrl.commons import profiler
        profiler.start()
    NS.monitoring.config.save()
    NS.monitoring.definitions.save()
    NS.sync_thread = sync.MonitoringIntegrationSdsSyncThread()

    monitoring_integration_manager = MonitoringIntegrationManager()
    monitoring_integration_manager.start()
    complete = threading.Event()
    NS.node_context = NS.node_context.load()
    current_tags = list(NS.node_context.tags)
    current_tags += ["tendrl/integration/monitoring"]
    NS.node_context.tags = list(set(current_tags))
    NS.node_context.save()

    def shutdown(signum, frame):
        complete.set()
        NS.sync_thread.stop()
        
    def reload_config(signum, frame):
        NS.monitoring.ns.setup_common_objects()
        
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGHUP, reload_config)

    while not complete.is_set():
        complete.wait(timeout=1)


if __name__ == '__main__':
    main()

import signal
import threading
import time

from tendrl.commons import manager as common_manager
from tendrl.commons import TendrlNS
from tendrl.commons.utils import log_utils as logger
from tendrl import monitoring_integration
from tendrl.monitoring_integration.grafana import \
    alert_organization
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration import sync
from tendrl.monitoring_integration.webhook import webhook_receiver


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
        # Creating Default Dashboards
        dashboard.upload_default_dashboards()
        # Create alert organization
        alert_organization.create()
        super(MonitoringIntegrationManager, self).start()
        # start webhook for receive alert from grafana
        self.webhook_receiver.start()

    def stop(self):
        self.webhook_receiver.stop()
        super(MonitoringIntegrationManager, self).stop()


def main():
    monitoring_integration.MonitoringIntegrationNS()

    TendrlNS()
    grafana_conn_count = 0
    while grafana_conn_count < 10:
        if not utils.port_open(
            NS.config.data["grafana_port"],
            NS.config.data["grafana_host"]
        ):
            grafana_conn_count = grafana_conn_count + 1
            time.sleep(4)
        else:
            break
    if grafana_conn_count == 10:
        logger.log("error", NS.get("publisher_id", None),
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
        monitoring_integration_manager.stop()
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

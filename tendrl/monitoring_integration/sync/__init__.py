import gevent

from tendrl.commons import sds_sync
from tendrl.monitoring_integration.grafana import webhook_receiver


class MonitoringIntegrationSdsSyncThread(sds_sync.StateSyncThread):

    def __init__(self):
        super(MonitoringIntegrationSdsSyncThread, self).__init__()
        self._complete = gevent.event.Event()

    def _run(self):
        while not self._complete.is_set():
            webhook_receiver.start_server()


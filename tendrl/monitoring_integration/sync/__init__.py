import gevent

from tendrl.commons import sds_sync

# TODO(Rishubh) Add grafana webhook to this greenlet
class MonitoringIntegrationSdsSyncThread(sds_sync.StateSyncThread):

    def __init__(self):
        super(MonitoringIntegrationSdsSyncThread, self).__init__()
        self._complete = gevent.event.Event()

    def _run(self):
        pass


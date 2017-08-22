import gevent
import etcd


from tendrl.commons import sds_sync
from tendrl.monitoring_integration.graphite import GraphitePlugin
from tendrl.monitoring_integration.graphite import graphite_utils
from tendrl.commons.utils import etcd_utils
from tendrl.commons.utils import log_utils as logger


class MonitoringIntegrationSdsSyncThread(sds_sync.StateSyncThread):

    def __init__(self):
        super(MonitoringIntegrationSdsSyncThread, self).__init__()
        self._complete = gevent.event.Event()

    def _run(self):
        interval = etcd_utils.read("_NS/gluster/config/data/sync_interval")

        try:
            interval = float(interval.value)
        except ValueError as ex:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': str(ex)})
            raise ex

        
        plugin_obj = GraphitePlugin()
        objects  = NS.monitoring.definitions.get_parsed_defs()["namespace.monitoring"]["graphite_data"]

        while not self._complete.is_set():
            try:
                gevent.sleep(interval)
                cluster_details = plugin_obj.get_data(objects)
                metrics = graphite_utils.create_metrics(objects, cluster_details)
                for metric in metrics:
                   for key, value in metric.items():
                       if value:
                           respose = plugin_obj.push_metrics(key, value)       
            except (etcd.EtcdKeyNotFound, AttributeError, KeyError) as ex:
                logger.log("error", NS.get("publisher_id", None),
                          {'message': str(ex)})

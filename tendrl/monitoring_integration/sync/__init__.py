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
        self.plugin_obj = GraphitePlugin()
        self.sync_interval = None

    def _run(self):
        while not self._complete.is_set():
            if self.sync_interval is None:
                try:
                    interval = etcd_utils.read("_NS/gluster/config/data/sync_interval")
                    try:
                        self.sync_interval = float(interval.value)
                    except ValueError as ex:
                        logger.log("error", NS.get("publisher_id", None),
                               {'message': "Unable to parse tendrl-gluster-integration config 'sync_interval' (value: %s)" % interval.value})
                        raise ex
                except etcd.EtcdKeyNotFound as ex:
                    continue

            aggregate_gluster_objects  = NS.monitoring.definitions.get_parsed_defs()["namespace.monitoring"]["graphite_data"]

            try:
                gevent.sleep(self.sync_interval)
                cluster_details = self.plugin_obj.get_central_store_data(aggregate_gluster_objects)
                metrics = graphite_utils.create_metrics(aggregate_gluster_objects, cluster_details)
                for metric in metrics:
                   for key, value in metric.items():
                       if value:
                           respose = self.plugin_obj.push_metrics(key, value)       
            except (etcd.EtcdKeyNotFound, AttributeError, KeyError) as ex:
                logger.log("error", NS.get("publisher_id", None),
                          {'message': str(ex)})

    def stop(self):
        super(MonitoringIntegrationSdsSyncThread, self).stop()
        self.plugin_obj.graphite_sock.shutdown()
        self.plugin_obj.graphite_sock.close()

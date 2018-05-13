import copy
import etcd
import socket
import time

from tendrl.commons.utils import etcd_utils
from tendrl.commons.utils import log_utils as logger


class GraphitePlugin(object):

    def __init__(self):

        self.host = NS.config.data["datasource_host"]
        self.port = NS.config.data["datasource_port"]
        self.carbon_port = NS.config.data["carbon_port"]
        self.prefix = 'tendrl'
        self._connect()

    def _connect(self):

        try:
            self.graphite_sock = socket.socket()
            self.graphite_sock.connect((
                self.host, int(self.carbon_port)))
        except socket.error as ex:
            logger.log(
                "error",
                NS.get("publisher_id", None),
                {'message': "Cannot connect to graphite "
                 "socket" + str(ex)})
            raise ex

    def _resend(self, message):

        try:
            self._connect()
            self.graphite_sock.sendall(message)
        except socket.error as ex:
            logger.log(
                "error",
                NS.get("publisher_id", None),
                {'message': "Cannot send data to graphite "
                 "socket" + str(ex)})
            raise ex

    def push_metrics(self, metric_name, metric_value):

        message = '%s%s%s %s %d\n' % (
            self.prefix,
            str("."),
            metric_name,
            str(metric_value),
            int(time.time())
        )
        try:
            response = self.graphite_sock.sendall(message)
        except socket.error:
            response = self._resend(message)
        return response

    def get_resource_count(self, resource_details, obj_attr):
        total = 0
        up = 0
        down = 0
        partial = 0
        created = 0
        stopped = 0
        paused = 0
        for key, value in obj_attr["count"].items():
            for resource_detail in resource_details["details"]:
                if key == "total":
                    total = total + 1
                if key == "up":
                    for attr_key, attr_values in obj_attr[
                            "count"]["up"].items():
                        if resource_detail[attr_key] in attr_values:
                            up = up + 1
                if key == "down":
                    for attr_key, attr_values in obj_attr[
                            "count"]["down"].items():
                        if resource_detail[attr_key] in attr_values:
                            down = down + 1
                if key == "partial":
                    for attr_key, attr_values in obj_attr[
                            "count"]["partial"].items():
                        if resource_detail[attr_key] in attr_values:
                            partial = partial + 1
                if key == "created":
                    for attr_key, attr_values in obj_attr[
                            "count"]["created"].items():
                        if resource_detail[attr_key] in attr_values:
                            created = created + 1
                if key == "stopped":
                    for attr_key, attr_values in obj_attr[
                            "count"]["stopped"].items():
                        if resource_detail[attr_key] in attr_values:
                            stopped = stopped + 1
                if key == "paused":
                    for attr_key, attr_values in obj_attr[
                            "count"]["paused"].items():
                        if resource_detail[attr_key] in attr_values:
                            paused = paused + 1
        resource_details["total"] = total
        resource_details["up"] = up
        resource_details["down"] = down
        resource_details["partial"] = partial
        resource_details["paused"] = paused
        resource_details["created"] = created
        resource_details["stopped"] = stopped
        return resource_details

    def get_object_from_central_store(
        self,
        obj_cls,
        obj_attr,
        integration_id,
        vol_id
    ):
        resource_details = {"details": []}
        if obj_cls in NS.tendrl.objects:
            _objs = NS.tendrl.objects[obj_cls](
                vol_id,
                integration_id=integration_id
            ).load_all()
            if _objs:
                for _obj in _objs:
                    resource_detail = {}
                    for key, value in obj_attr['attrs'].items():
                        resource_detail[key] = getattr(_obj, key)
                    resource_details["details"].append(resource_detail)
        try:
            if obj_attr["count"]:
                resource_details = self.get_resource_count(
                    resource_details,
                    obj_attr
                )
        except KeyError:
            pass

        return resource_details

    def get_central_store_data(self, objects):
        try:
            _clusters = NS.tendrl.objects.Cluster().load_all()
            cluster_data = []
            for _cluster in _clusters:
                if _cluster.is_managed in [None, "no"]:
                    continue
                cluster_details = {}
                cluster_details["integration_id"] = _cluster.integration_id
                cluster_details["short_name"] = _cluster.short_name
                cluster_details["Cluster"] = self.get_cluster_details(
                    objects, _cluster.integration_id
                )
                cluster_details["Brick"] = self.get_brick_details(
                    objects, _cluster.integration_id
                )
                cluster_details["Volume"] = self.get_volume_details(
                    objects, _cluster.integration_id
                )
                cluster_details["Node"] = self.get_node_details(
                    objects, _cluster.integration_id
                )
                cluster_data.append(copy.deepcopy(cluster_details))
            try:
                cluster_data = self.set_volume_count(cluster_data, "Volume")
                cluster_data = self.set_resource_count(cluster_data, "Node")
                cluster_data = self.set_resource_count(cluster_data, "Brick")
                cluster_data = self.set_brick_count(cluster_data)
                cluster_data = self.set_brick_path(cluster_data)
                cluster_data = self.set_geo_rep_session(cluster_data)
                cluster_data = self.set_volume_level_brick_count(cluster_data)
            except (etcd.EtcdKeyNotFound, AttributeError, KeyError) as ex:
                logger.log(
                    "debug",
                    NS.get("publisher_id", None),
                    {
                        'message': "Failed to set resource details" + str(ex)
                    }
                )
            return cluster_data
        except (etcd.EtcdException, AttributeError, KeyError) as ex:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': str(ex)})
            raise ex

    def get_cluster_details(self, objects, integration_id):
        cluster_detail = []
        for obj in objects["Cluster"]:
            if obj in ["metric", "value"]:
                continue
            resource_detail = {}
            resource_detail[str(obj)] = {}
            obj_details = objects["Cluster"][str(obj)]
            obj_attrs = obj_details["attrs"]
            _resource_obj = NS.tendrl.objects[str(obj)](
                integration_id=integration_id
            ).load()
            for key, _ in obj_attrs.items():
                attr_value = self.cluster_status_mapper(
                    str(getattr(_resource_obj, key))
                )
                resource_detail[str(obj)][key] = copy.deepcopy(
                    attr_value
                )
            if not resource_detail == {}:
                cluster_detail.append(resource_detail)
        return cluster_detail

    def get_brick_details(self, objects, integration_id):
        brick_detail = []
        _cluster_node_ids = etcd_utils.read(
            "/clusters/%s/nodes" % integration_id
        )
        for _node_id in _cluster_node_ids.leaves:
            _cnc = NS.tendrl.objects.ClusterNodeContext(
                integration_id=integration_id,
                node_id=_node_id.key.split('/')[-1]
            ).load()
            _bricks = NS.tendrl.objects.GlusterBrick(
                integration_id,
                _cnc.fqdn
            ).load_all() or []
            for _brick in _bricks:
                resource_detail = {}
                resource_detail["host_name"] = _cnc.fqdn.replace(".", "_")
                if _brick.deleted in ['true', 'True', 'TRUE']:
                    continue
                for key, _ in objects["Brick"]["attrs"].items():
                    brick_attr_value = self.resource_status_mapper(
                        str(getattr(_brick, key))
                    )
                    resource_detail[key] = brick_attr_value
                if not resource_detail == {}:
                    brick_detail.append(resource_detail)
        return brick_detail

    def get_volume_details(self, objects, integration_id):
        volume_detail = []
        _volumes = NS.tendrl.objects.GlusterVolume(
            integration_id=integration_id
        ).load_all() or []
        for _volume in _volumes:
            resource_detail = {}
            if _volume.deleted in ['true', 'True', 'TRUE'] or \
                    _volume.name is None:
                continue
            for key, value in objects["Volume"]["attrs"].items():
                if value is None:
                    attr_value = self.resource_status_mapper(
                        str(getattr(_volume, key))
                    )
                    resource_detail[key] = attr_value
                else:
                    try:
                        resp_data = self.get_object_from_central_store(
                            key,
                            objects["Volume"]["attrs"][key],
                            integration_id,
                            _volume.vol_id
                        )
                        resource_detail[key] = resp_data
                    except (etcd.EtcdKeyNotFound,
                            AttributeError,
                            KeyError):
                        resource_detail[key] = {
                            "total": 0,
                            "up": 0,
                            "down": 0,
                            "partial": 0,
                            "created": 0,
                            "stopped": 0,
                            "paused": 0
                        }
            if not resource_detail == {}:
                volume_detail.append(resource_detail)
        return volume_detail

    def get_node_details(self, objects, integration_id):
        node_detail = []
        _cluster_node_ids = etcd_utils.read(
            "/clusters/%s/nodes" % integration_id
        )
        for _node_id in _cluster_node_ids.leaves:
            _cnc = NS.tendrl.objects.ClusterNodeContext(
                integration_id=integration_id,
                node_id=_node_id.key.split('/')[-1]
            ).load()
            if _cnc.is_managed != "yes":
                continue
            resource_detail = {}
            for key, value in objects["Node"]["attrs"].items():
                if value is None:
                    attr_value = getattr(_cnc, key)
                    if attr_value not in [None, ""]:
                        attr_value = self.resource_status_mapper(
                            str(getattr(_cnc, key))
                        )
                        resource_detail[key] = attr_value
                    else:
                        if key == 'status':
                            _node_context = NS.tendrl.objects.NodeContext(
                                node_id=_cnc.node_id
                            ).load()
                            attr_value = self.resource_status_mapper(
                                str(getattr(_node_context, 'status'))
                            )
                            resource_detail[key] = attr_value
            node_detail.append(resource_detail)
        return node_detail

    def set_geo_rep_session(self, cluster_data):
        for cluster in cluster_data:
            # Initialize the counts map
            geo_rep_mapper = {
                "total": 0,
                "partial": 0,
                "up": 0,
                "down": 0,
                "created": 0,
                "stopped": 0,
                "paused": 0
            }
            for volume in cluster["Volume"]:
                try:
                    for key, value in volume["geo_rep_session"].items():
                        try:
                            geo_rep_mapper[key] = geo_rep_mapper[key] + value
                        except (AttributeError, KeyError) as ex:
                            logger.log(
                                "debug",
                                NS.get("publisher_id", None),
                                {
                                    'message': "Failed to extract georep "
                                    "details for {0}".format(key) + str(ex)
                                }
                            )
                except (AttributeError, KeyError) as ex:
                        logger.log(
                            "debug",
                            NS.get("publisher_id", None),
                            {
                                'message': "Failed to extract georep details "
                                "for volume" + str(ex)
                            }
                        )
            cluster["geo_rep"] = {
                "total": geo_rep_mapper["total"],
                "up": geo_rep_mapper["up"],
                "down": geo_rep_mapper["down"],
                "partial": geo_rep_mapper["partial"],
                "created": geo_rep_mapper["created"],
                "stopped": geo_rep_mapper["stopped"],
                "paused": geo_rep_mapper["paused"]
            }
        return cluster_data

    def set_volume_level_brick_count(self, cluster_data):
        for cluster in cluster_data:
            volume_detail = {}
            for volume in cluster["Volume"]:
                try:
                    volume_detail[volume["name"]] = {"total": 0,
                                                     "up": 0,
                                                     "down": 0}
                except (AttributeError, KeyError):
                    pass
            # Increment count using volume_details
            for brick in cluster["Brick"]:
                try:
                    volume_detail[str(brick["vol_name"])]["total"] = \
                        volume_detail[str(brick["vol_name"])]["total"] + 1
                    if brick["status"] == 0 or brick["status"] == 1:
                        volume_detail[str(brick["vol_name"])]["up"] = \
                            volume_detail[str(brick["vol_name"])]["up"] + 1
                    else:
                        volume_detail[str(brick["vol_name"])]["down"] = \
                            volume_detail[str(brick["vol_name"])]["down"] + 1
                except (AttributeError, KeyError) as ex:
                    logger.log(
                        "debug",
                        NS.get("publisher_id", None),
                        {
                            'message': "Failed to set volume level "
                            "brick count" + str(
                                ex)
                        }
                    )
            cluster["volume_level_brick_count"] = volume_detail
        return cluster_data

    def set_brick_count(self, cluster_data):
        for cluster in cluster_data:
            for node in cluster["Node"]:
                try:
                    total = 0
                    up = 0
                    down = 0
                    for brick in cluster["Brick"]:
                        if(
                            brick["host_name"] ==
                                node["fqdn"].replace(".", "_")
                        ):
                            if brick["status"] == 0 or brick["status"] == 1:
                                total = total + 1
                                up = up + 1
                            else:
                                total = total + 1
                                down = down + 1
                    node["brick_total_count"] = total
                    node["brick_up_count"] = up
                    node["brick_down_count"] = down
                except (AttributeError, KeyError) as ex:
                    logger.log(
                        "debug",
                        NS.get("publisher_id", None),
                        {'message': "Failed to set brick count" + str(ex)}
                    )
        return cluster_data

    def set_brick_path(self, cluster_data):
        for cluster in cluster_data:
            for brick in cluster["Brick"]:
                try:
                    brick["brick_name"] = brick["brick_path"].split(":")[1]
                except (AttributeError, KeyError) as ex:
                    logger.log(
                        "debug",
                        NS.get("publisher_id", None),
                        {'message': "Failed to set brick path" + str(ex)}
                    )
        return cluster_data

    def set_resource_count(self, cluster_data, resource_name):
        for cluster in cluster_data:
            resources = cluster[str(resource_name)]
            cluster[
                str(resource_name).lower() + "_total_count"] = len(resources)
            up = 0
            down = 0
            for resource in resources:
                try:
                    if resource["status"] == 0 or resource["status"] == 1:
                        up = up + 1
                    else:
                        down = down + 1
                except KeyError as ex:
                    logger.log(
                        "debug",
                        NS.get("publisher_id", None),
                        {
                            'message': "Failed to set resource count "
                            "for {0}".format(resource_name) + str(ex)
                        }
                    )
            cluster[str(resource_name).lower() + "_up_count"] = up
            cluster[str(resource_name).lower() + "_down_count"] = down
        return cluster_data

    def set_volume_count(self, cluster_data, resource_name):
        for cluster in cluster_data:
            resources = cluster[str(resource_name)]
            cluster[str(
                resource_name).lower() + "_total_count"] = len(resources)
            up = 0
            down = 0
            partial = 0
            degraded = 0
            for resource in resources:
                try:
                    if resource["state"] == 0 or resource["state"] == 1:
                        up = up + 1
                    elif resource["state"] == 4:
                        partial = partial + 1
                    elif resource["state"] == 3:
                        degraded = degraded + 1
                    else:
                        down = down + 1
                except KeyError as ex:
                    logger.log(
                        "debug",
                        NS.get("publisher_id", None),
                        {
                            'message': "Failed to set resource count "
                            "for {0}".format(resource_name) + str(ex)
                        }
                    )
            cluster[str(
                resource_name).lower() + "_up_count"] = up
            cluster[str(
                resource_name).lower() + "_down_count"] = down
            cluster[str(
                resource_name).lower() + "_partial_count"] = partial
            cluster[str(
                resource_name).lower() + "_degraded_count"] = degraded
        return cluster_data

    def resource_status_mapper(self, status):
        status_map = {"started": 0,
                      "up": 0,
                      "(degraded)": 3,
                      "degraded": 3,
                      "(partial)": 4,
                      "partial": 4,
                      "unknown": 5,
                      "failed": 7,
                      "down": 8,
                      "created": 9,
                      "stopped": 8,
                      "completed": 12,
                      "not started": 13,
                      "not_started": 13,
                      "in progress": 14,
                      "in_progress": 14,
                      "paused": 15,
                      "layout_fix_started": 16,
                      "layout_fix_stopped": 17,
                      "layout_fix_complete": 18,
                      "layout_fix_failed": 19
                      }
        try:
            temp_status = copy.deepcopy(status).lower()
            return status_map[temp_status]
        except KeyError:
            return status

    def cluster_status_mapper(self, status):
        status_map = {"healthy": 0, "unhealthy": 2}
        try:
            return "unhealthy" if not status else status_map[status]
        except KeyError:
            return status

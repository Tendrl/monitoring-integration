import copy
import os
import socket
import time


import etcd


from tendrl.commons.utils import etcd_utils
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import cluster_detail


class GraphitePlugin():

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
        resource_details["total"] = total
        resource_details["up"] = up
        resource_details["down"] = down
        resource_details["partial"] = partial
        return resource_details

    def get_object_from_central_store(self, resource_key, obj_attr):
        attr_details = etcd_utils.read(resource_key)
        resource_details = {"details": []}
        for attr_detail in attr_details.leaves:
            resource_detail = {}
            attr_key = attr_detail.key.rsplit("/", 1)[1]
            for key, value in obj_attr["attrs"].items():
                sub_attr = etcd_utils.read(
                    os.path.join(resource_key, attr_key, key))
                resource_detail[key] = sub_attr.value
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

    def get_resource_keys(self, key, resource_name):

        resource_list = []
        try:
            resource_details = etcd_utils.read(key + "/" + str(
                resource_name))
            for resource in resource_details.leaves:
                resource_list.append(resource.key.split('/')[-1])
        except (KeyError, etcd.EtcdKeyNotFound) as ex:
            logger.log(
                "error",
                NS.get("publisher_id", None),
                {
                    'message': "Error while fetching " +
                    str(resource_name).split('/')[0] + str(ex)
                }
            )

        return resource_list

    def get_central_store_data(self, objects):
        try:
            cluster_list = self.get_resource_keys("", "clusters")
            cluster_data = []
            for cluster_id in cluster_list:
                try:
                    cluster_key = "/clusters/" + str(
                        cluster_id) + "/is_managed"
                    cluster_is_managed = etcd_utils.read(
                        cluster_key).value
                    if cluster_is_managed.lower() == "no":
                        continue
                except etcd.EtcdKeyNotFound:
                    continue
                cluster_details = cluster_detail.ClusterDetail()
                cluster_details.integration_id = cluster_id
                cluster_key = objects["Cluster"]["value"].replace(
                    "$integration_id",
                    cluster_details.integration_id
                )
                for obj in objects["Cluster"]:
                    if obj in ["metric", "value"]:
                        continue
                    resource_detail = {}
                    resource_detail[str(obj)] = {}
                    obj_details = objects["Cluster"][str(obj)]
                    obj_key = os.path.join(cluster_key, str(obj))
                    obj_attrs = obj_details["attrs"]
                    for key, value in obj_attrs.items():
                        try:
                            attr_key = os.path.join(obj_key, key)
                            attr_data = etcd_utils.read(attr_key)
                            attr_value = self.cluster_status_mapper(
                                str(attr_data.value).lower())
                            resource_detail[str(obj)][key] = copy.deepcopy(
                                attr_value)
                        except (KeyError, etcd.EtcdKeyNotFound) as ex:
                            logger.log(
                                "error",
                                NS.get("publisher_id", None),
                                {
                                    'message': "Cannot Find {0} in Cluster "
                                    "{1}".format(key, cluster_id) + str(ex)
                                }
                            )
                    cluster_details.details["Cluster"].append(
                        copy.deepcopy(resource_detail))
                host_list = self.get_resource_keys(cluster_key, "Bricks/all")
                for host in host_list:
                    resource_detail = {}
                    attr_key = os.path.join(cluster_key, "Bricks/all", host)
                    resource_detail["host_name"] = host.replace(".", "_")
                    brick_list = self.get_resource_keys("", attr_key)
                    for brick in brick_list:
                        brick_deleted_key = os.path.join(cluster_key, "Bricks/all",
                                                         host, brick, "deleted")
                        try:
                            is_brick_deleted = etcd_utils.read(brick_deleted_key).value
                            if is_brick_deleted.lower() == "true":
                                continue
                        except etcd.EtcdKeyNotFound:
                            continue
                        for key, value in objects["Brick"]["attrs"].items():
                            try:
                                brick_attr_key = os.path.join(cluster_key,
                                                              "Bricks/all",
                                                              host, brick, key)
                                brick_attr_data = etcd_utils.read(
                                    brick_attr_key)
                                brick_attr_value = self.resource_status_mapper(
                                    str(brick_attr_data.value).lower())
                                resource_detail[key] = brick_attr_value
                            except (KeyError, etcd.EtcdKeyNotFound) as ex:
                                logger.log(
                                    "error",
                                    NS.get("publisher_id", None),
                                    {
                                        'message': "Cannot Find {0} in brick "
                                        "{1}".format(key, brick) + str(ex)
                                    }
                                )
                        cluster_details.details["Brick"].append(
                            copy.deepcopy(resource_detail))
                volume_list = self.get_resource_keys(cluster_key, "Volumes")
                for volume in volume_list:
                    resource_detail = {}
                    volume_key = os.path.join(cluster_key, "Volumes", volume)
                    volume_deleted_key = os.path.join(volume_key, "deleted")
                    try:
                        is_volume_deleted = etcd_utils.read(volume_deleted_key).value
                        if is_volume_deleted.lower() == "true":
                            continue
                    except etcd.EtcdKeyNotFound:
                        continue
                    for key, value in objects["Volume"]["attrs"].items():
                        if value is None:
                            try:
                                attr_key = os.path.join(volume_key, key)
                                attr_data = etcd_utils.read(attr_key)
                                attr_value = self.resource_status_mapper(
                                    str(attr_data.value).lower())
                                resource_detail[key] = attr_value
                            except (KeyError, etcd.EtcdKeyNotFound) as ex:
                                logger.log(
                                    "error",
                                    NS.get("publisher_id", None),
                                    {
                                        'message': "Cannot Find {0} in volume "
                                        "{1}".format(key, volume) + str(ex)
                                    }
                                )
                        else:
                            try:
                                new_key = os.path.join(
                                    volume_key, objects["Volume"]["attrs"][
                                        key]["value"].rsplit("/", 1)[1])
                                resp_data = self.get_object_from_central_store(
                                    new_key, objects["Volume"]["attrs"][key])
                                resource_detail[key] = resp_data
                            except (etcd.EtcdKeyNotFound,
                                    AttributeError,
                                    KeyError) as ex:
                                logger.log(
                                    "error",
                                    NS.get("publisher_id", None),
                                    {
                                        'message': "Error in retreiving "
                                        "geo_replication data for "
                                        "volume" + str(volume) + str(ex)
                                    }
                                )
                                resource_detail[key] = {"total": 0,
                                                        "up": 0,
                                                        "down": 0,
                                                        "partial": 0}
                    cluster_details.details["Volume"].append(
                        copy.deepcopy(resource_detail))
                node_list = self.get_resource_keys(cluster_key, "nodes")
                for node in node_list:
                    resource_detail = {}
                    node_key = objects["Node"]["value"].replace(
                        "$integration_id",
                        cluster_details.integration_id
                    ).replace("$node_id", node)
                    for key, value in objects["Node"]["attrs"].items():
                        if value is None:
                            try:
                                attr_key = os.path.join(node_key, key)
                                attr_data = etcd_utils.read(attr_key)
                                attr_value = self.resource_status_mapper(
                                    str(attr_data.value).lower())
                                resource_detail[key] = attr_value
                            except (etcd.EtcdKeyNotFound,
                                    AttributeError,
                                    KeyError) as ex:
                                if key == 'status':
                                    node_status_key = os.path.join(
                                        "nodes",
                                        node,
                                        "NodeContext",
                                        "status"
                                    )
                                    try:
                                        node_status_value = etcd_utils.read(node_status_key).value
                                        attr_value = self.resource_status_mapper(
                                            node_status_value.lower()
                                        )
                                        resource_detail[key] = attr_value
                                    except etcd.EtcdKeyNotFound:
                                        pass
                                logger.log(
                                    "error",
                                    NS.get("publisher_id", None),
                                    {
                                        'message': "Cannot Find {0} in "
                                        "Node {1}".format(key, node) + str(ex)
                                    }
                                )
                    cluster_details.details["Node"].append(
                        copy.deepcopy(resource_detail))
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
                    "error",
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

    def set_geo_rep_session(self, cluster_data):
        total = 0
        partial = 0
        up = 0
        down = 0
        geo_rep_mapper = {"total": total, "partial": partial, "up": up,
                          "down": down}
        for cluster in cluster_data:
            for volume in cluster.details["Volume"]:
                try:
                    for key, value in volume["geo_rep_session"].items():
                        try:
                            geo_rep_mapper[key] = geo_rep_mapper[key] + value
                        except (AttributeError, KeyError) as ex:
                            logger.log(
                                "error",
                                NS.get("publisher_id", None),
                                {
                                    'message': "Failed to extract georep "
                                    "details for {0}".format(key) + str(ex)
                                }
                            )
                except (AttributeError, KeyError) as ex:
                        logger.log(
                            "error",
                            NS.get("publisher_id", None),
                            {
                                'message': "Failed to extract georep details "
                                "for volume" + str(ex)
                            }
                        )
            cluster.details["geo_rep"] = {}
            cluster.details["geo_rep"]["total"] = geo_rep_mapper["total"]
            cluster.details["geo_rep"]["up"] = geo_rep_mapper["up"]
            cluster.details["geo_rep"]["down"] = geo_rep_mapper["down"]
            cluster.details["geo_rep"]["partial"] = geo_rep_mapper["partial"]
        return cluster_data

    def set_volume_level_brick_count(self, cluster_data):
        volume_detail = {}
        for cluster in cluster_data:
            for volume in cluster.details["Volume"]:
                try:
                    volume_detail[volume["name"]] = {"total": 0,
                                                     "up": 0,
                                                     "down": 0}
                except (AttributeError, KeyError):
                    pass
        for cluster in cluster_data:
            for brick in cluster.details["Brick"]:
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
                        "error",
                        NS.get("publisher_id", None),
                        {
                            'message': "Failed to set volume level "
                            "brick count" + str(
                                ex)
                        }
                    )
            cluster.details["volume_level_brick_count"] = volume_detail
        return cluster_data

    def set_brick_count(self, cluster_data):
        for cluster in cluster_data:
            for node in cluster.details["Node"]:
                try:
                    total = 0
                    up = 0
                    down = 0
                    for brick in cluster.details["Brick"]:
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
                        "error",
                        NS.get("publisher_id", None),
                        {'message': "Failed to set brick count" + str(ex)}
                    )
        return cluster_data

    def set_brick_path(self, cluster_data):
        for cluster in cluster_data:
            for brick in cluster.details["Brick"]:
                try:
                    brick["brick_name"] = brick["brick_path"].split(":")[1]
                except (AttributeError, KeyError) as ex:
                    logger.log(
                        "error",
                        NS.get("publisher_id", None),
                        {'message': "Failed to set brick path" + str(ex)}
                    )
        return cluster_data

    def set_resource_count(self, cluster_data, resource_name):
        for cluster in cluster_data:
            resources = cluster.details[str(resource_name)]
            cluster.details[
                str(resource_name.lower()) + "_total_count"] = len(resources)
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
                        "error",
                        NS.get("publisher_id", None),
                        {
                            'message': "Failed to set resource count "
                            "for {0}".format(resource_name) + str(ex)
                        }
                    )
            cluster.details[str(resource_name.lower()) + "_up_count"] = up
            cluster.details[str(resource_name.lower()) + "_down_count"] = down
        return cluster_data

    def set_volume_count(self, cluster_data, resource_name):
        for cluster in cluster_data:
            resources = cluster.details[str(resource_name)]
            cluster.details[str(
                resource_name.lower()) + "_total_count"] = len(resources)
            up = 0
            down = 0
            partial = 0
            degraded = 0
            for resource in resources:
                try:
                    if resource["state"] == 0 or resource["state"] == 1 :
                        up = up + 1
                    elif resource["state"] == 4:
                        partial = partial + 1
                    elif resource["state"] == 3:
                        degraded = degraded + 1
                    else:
                        down = down + 1
                except KeyError as ex:
                    logger.log(
                        "error",
                        NS.get("publisher_id", None),
                        {
                            'message': "Failed to set resource count "
                            "for {0}".format(resource_name) + str(ex)
                        }
                    )
            cluster.details[str(
                resource_name.lower()) + "_up_count"] = up
            cluster.details[str(
                resource_name.lower()) + "_down_count"] = down
            cluster.details[str(
                resource_name.lower()) + "_partial_count"] = partial
            cluster.details[str(
                resource_name.lower()) + "_degraded_count"] = degraded
        return cluster_data

    def resource_status_mapper(self, status):
        status_map = {"started": 1, "up": 0, "(degraded)": 3, "degraded": 3,
                      "(partial)": 4, "unknown": 5, "failed": 7, "down": 8,
                      "created": 9, "stopped" : 10, "completed": 12,
                      "not started": 13,
                      "not_started": 13, "in progress": 14,
                      "in_progress": 14}
        try:
            return status_map[status]
        except KeyError:
            return status

    def cluster_status_mapper(self, status):
        status_map = {"healthy": 0, "unhealthy": 2}
        try:
            return status_map[status]
        except KeyError:
            return status

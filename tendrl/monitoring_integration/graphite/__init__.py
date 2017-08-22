import os
import copy


import etcd
import time
import socket


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
            self.graphite_sock.connect((self.host, int(self.carbon_port)))
        except socket.error as ex:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': "Cannot connect to graphite socket" + str(ex)})
            raise ex
            

    def push_metrics(self, metric_name, metric_value):

        message = '%s%s%s %s %d\n' % (
            self.prefix,
            str("."),
            metric_name,
            str(metric_value),
            int(time.time())
        )
        
        response = self.graphite_sock.sendall(message)
        return response
            

    def get_count(self,resource_details, obj_attr):
        total = 0 
        up = 0
        down = 0
        for key, value in obj_attr["count"].items():
            for resource_detail in resource_details["details"]:
                if key == "total":
                   total = total + 1
                if key == "up":
                   for attr_key, attr_values in obj_attr["count"]["up"].items():
                       if resource_detail[attr_key] in attr_values:
                           up = up + 1
                if key == "down":
                   for attr_key, attr_values in obj_attr["count"]["down"].items():
                       if resource_detail[attr_key] in attr_values:
                           down = down + 1
        resource_details["total"] = total
        resource_details["up"] = up
        resource_details["down"] = down

    def read_data(self, resource_key, obj_attr):
        attr_details = etcd_utils.read(resource_key)
        resource_details = {"details" : []}
        for attr_detail in attr_details.leaves:
             resource_detail = {}
             attr_key = attr_detail.key.rsplit("/", 1)[1]
             for key, value in obj_attr["attrs"].items():
                 sub_attr = etcd_utils.read(os.path.join(resource_key, attr_key, key))
                 resource_detail[key] = sub_attr.value
             resource_details["details"].append(resource_detail)
        try:
            if obj_attr["count"]:
                self.get_count(resource_details, obj_attr)
        except KeyError:
            pass
        return resource_details
                 

    def get_data(self, objects):
        try:
            clusters = etcd_utils.read('clusters')
            cluster_data = []
            for cluster in clusters.leaves:
                cluster_details = cluster_detail.ClusterDetail()
                cluster_details.integration_id = cluster.key.split('/')[-1]

                for obj in objects:
                    resource_detail = {}
                    obj_details = objects[str(obj)]
                    cluster_key = obj_details["value"].replace("$integration_id", cluster_details.integration_id)
                    obj_attrs = obj_details["attrs"]
                    if str(obj_details["value"]).count("$") > 1:
                        obj_key = cluster_key.rsplit("/", 1)[0]
                        resources = etcd_utils.read(obj_key)
                        for resource in resources.leaves:
                            for key, value in obj_attrs.items():
                                if value is not None:
                                    attr_key = obj_attrs[key]["value"]
                                    status_key = os.path.join(obj_key,resource.key.rsplit("/", 1)[1], attr_key.rsplit('/', 1)[1])
                                    try:
                                        resp_data = self.read_data(status_key, obj_attrs[key])
                                        resource_detail[key] = resp_data
                                    except etcd.EtcdKeyNotFound:
                                        resource_detail[key] = {"total": 0, "up": 0, "down": 0}
                                else:
                                    if obj == "Node":
                                        temp_resource_key = resource.key + "/NodeContext"
                                        status_key = os.path.join(obj_key, temp_resource_key, key)
                                    else:
                                        status_key = os.path.join(obj_key, resource.key.rsplit("/", 1)[1], key)
                                    resp_data = etcd_utils.read(status_key)
                                    status = self.resource_status_mapper(str(resp_data.value).lower())
                                    resource_detail[key] = status
                            cluster_details.details[obj].append(copy.deepcopy(resource_detail))
                    else:
                        for key, value in obj_attrs.items():
                            obj_key = os.path.join(cluster_key, key)
                            resp_data = etcd_utils.read(obj_key)
                            status = self.cluster_status_mapper(str(resp_data.value).lower())
                            resource_detail[key] = status
                                
                        cluster_details.details[obj].append(copy.deepcopy(resource_detail))
                cluster_data.append(copy.deepcopy(cluster_details))

        except (etcd.EtcdKeyNotFound, AttributeError, KeyError) as ex:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': str(ex)})
            raise ex
        return cluster_data

    def resource_status_mapper(self, status):
        status_map = {"created":3, "stopped":2, "started":0, "degraded": 1, "up": 0, "down": 1}
        try:
            return status_map[status]
        except KeyError:
            return status
        
    def cluster_status_mapper(self, status):
        status_map = {"healthy" : 1, "unhealthy" : 0}
        try:
            return status_map[status]
        except KeyError:
            return status


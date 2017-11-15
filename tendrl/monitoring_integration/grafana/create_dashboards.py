import copy
import json
import os


import etcd


from tendrl.monitoring_integration.grafana import cluster_detail
from tendrl.commons.utils import etcd_utils
from tendrl.monitoring_integration.grafana import utils
from tendrl.commons.utils import log_utils as logger


ATTRS = {"bricks": ["brick_path", "hostname", "vol_id", "vol_name"],
         "nodes": ["fqdn"],
         "volumes": ["name", "vol_id"]
         }



def get_resource_keys(key, resource_name):

    resource_list = []
    try:
        resource_details = etcd_utils.read(key + "/" + str(resource_name))
        for resource in resource_details.leaves:
            resource_list.append(resource.key.split('/')[-1])
    except (KeyError, etcd.EtcdKeyNotFound) as ex:
        logger.log("error", NS.get("publisher_id", None),
                   {'message': "Error while fetching " +
                    str(resource_name).split('/')[0] + str(ex)})

    return resource_list


def get_subvolume_details(key):
    subvolume_brick_details = []
    subvolumes = get_resource_keys(key, "Bricks")
    for subvolume in subvolumes:
        try:
            subvolume_details = {}
            subvolume_details["subvolume"] = ""
            subvolume_details["bricks"] = []
            subvolume_details["subvolume"] = subvolume
            brick_list = get_resource_keys(key + "/" + "Bricks", subvolume)
            subvolume_details["bricks"] = brick_list
            subvolume_brick_details.append(copy.deepcopy(subvolume_details))
        except (KeyError, etcd.EtcdKeyNotFound) as ex:
            logger.log("error", NS.get("publisher_id", None),
                       {'message': "Error while fetching "
                        "subvolumes" + str(ex)})

    return subvolume_brick_details


def get_cluster_details(integration_id=None):
    '''
        To get details of glusters from etcd
        TODO: Optimize the code, reduce number of etcd calls
        TODO: Extract etcd host and port from configuration file '''

    cluster_details_list = []
    try:
        cluster_list = []
        if integration_id:
            cluster_list.append(integration_id)
        else:
            cluster_list = get_resource_keys("", "clusters")
        for integration_id in cluster_list:
            try:
                cluster_key = "/clusters/" + str(integration_id) + "/is_managed"
                cluster_is_managed = etcd_utils.read(cluster_key).value
                if cluster_is_managed.lower() == "no":
                    continue
            except etcd.EtcdKeyNotFound:
                continue
            cluster_obj = cluster_detail.ClusterDetail()
            cluster_obj.integration_id = integration_id
            cluster_key = '/clusters/' + str(cluster_obj.integration_id)
            # Get node details
            cluster_obj.hosts = get_node_details(cluster_key)
            # Get volume details
            cluster_obj.volumes = get_volumes_details(cluster_key)
            # Get brick details from subvolumes
            cluster_obj.bricks = get_brick_details(cluster_obj.volumes)
            cluster_details_list.append(cluster_obj)
        return cluster_details_list
    except (etcd.EtcdKeyNotFound, KeyError) as ex:
        logger.log("error", NS.get("publisher_id", None),
                   {'message': str(ex)})
        return None


def get_node_details(cluster_key):
    node_details = []
    node_list = get_resource_keys(cluster_key, "nodes")
    for node_id in node_list:
        for attr in ATTRS["nodes"]:
            try:
                node = {}
                node[attr] = etcd_utils.read(
                    cluster_key  + "/nodes/" + str(node_id) + "/NodeContext/" + attr
                ).value
                node_details.append(node)
            except (KeyError, etcd.EtcdKeyNotFound) as ex:
                    logger.log("error", NS.get("publisher_id", None),
                               {'message': "Error while fetching "
                                "node id {}".format(node_id) + str(ex)})
    return node_details


def get_brick_details(volumes):
    brick_details = []
    
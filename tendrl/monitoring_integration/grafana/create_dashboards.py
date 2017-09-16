import copy
import json
import os


import etcd


from tendrl.monitoring_integration.grafana import cluster_detail
from tendrl.commons.utils import etcd_utils
from tendrl.monitoring_integration.grafana import utils
from tendrl.commons.utils import log_utils as logger


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
                       {'message': "Error while fetching subvolumes" + str(ex)})

    return subvolume_brick_details


def get_cluster_details(integration_id=None):
    ''' 
        To get details of glusters from etcd
        TODO: Optimize the code, reduce number of etcd calls 
        TODO: Extract etcd host and port from configuration file '''

    
    attrs = {"bricks" : ["brick_path", "hostname", "vol_id", "vol_name"],
             "nodes" : ["fqdn"], "volumes" : ["name","vol_id"]}
    cluster_details_list = []
    try:
        cluster_list = []
        if integration_id:
             cluster_list.append(integration_id)
        else:
             cluster_list = get_resource_keys("", "clusters")
        for cluster_id in cluster_list:
            try:
                cluster_key = "/clusters/" + str(cluster_id) + "/is_managed"
                cluster_is_managed = etcd_utils.read(cluster_key).value 
                if cluster_is_managed.lower() == "no":
                    continue
            except etcd.EtcdKeyNotFound: 
                continue 
            cluster_obj = cluster_detail.ClusterDetail()
            cluster_obj.integration_id =  cluster_id
            cluster_key = '/clusters/' + str(cluster_obj.integration_id)
            node_list = get_resource_keys(cluster_key, "Bricks/all")
            for node_id in node_list:
                node_key = os.path.join(cluster_key + "/Bricks/all/")
                brick_list = get_resource_keys(node_key, str(node_id))
                for brick_id in brick_list:
                    brick_key = os.path.join(node_key, str(node_id), brick_id)
                    try:
                        brick_details = etcd_utils.read(brick_key)
                        brick = {}
                        for brick_detail in brick_details.leaves:
                            try:
                                if brick_detail.key.rsplit('/')[-1] in attrs["bricks"]:
                                    if brick_detail.key.rsplit('/')[-1] == "brick_path":
                                        brick[brick_detail.key.rsplit('/')[-1]] = \
                                        brick_detail.value.split(":")[1].replace('/','|')
                                    else:
                                        brick[brick_detail.key.rsplit('/')[-1]] = \
                                            brick_detail.value
                            except (KeyError, etcd.EtcdKeyNotFound) as ex:
                                logger.log("error", NS.get("publisher_id", None),
                                          {'message': "Error while fetching brick_details" + str(ex)})
                        cluster_obj.bricks.append(copy.deepcopy(brick))
                    except (KeyError, etcd.EtcdKeyNotFound) as ex:
                        logger.log("error", NS.get("publisher_id", None),
                                   {'message': "Error while fetching brick id" + str(ex)})
            node_list = get_resource_keys(cluster_key, "nodes")
            for node_id in node_list:
                try:
                    node_details = etcd_utils.read(cluster_key + 
                                                   "/nodes/" + 
                                                   str(node_id) +
                                                   "/NodeContext")
                    nodes = {}
                    for node_detail in node_details.leaves:
                        try:
                            if node_detail.key.rsplit('/')[-1] in attrs["nodes"]:
                                nodes[node_detail.key.rsplit('/')[-1]] = \
                                    node_detail.value
                        except (KeyError, etcd.EtcdKeyNotFound) as ex:
                                logger.log("error", NS.get("publisher_id", None),
                                          {'message': "Error while fetching node_details" + str(ex)})
                  
                    cluster_obj.hosts.append(copy.deepcopy(nodes))
                except (KeyError, etcd.EtcdKeyNotFound) as ex:
                        logger.log("error", NS.get("publisher_id", None),
                                   {'message': "Error while fetching node id {}".format(node_id) + str(ex)})
            volume_list = get_resource_keys(cluster_key, "Volumes")
            for volume_id in volume_list:
                try:
                    volume_data = {}
                    volume_details = etcd_utils.read(cluster_key +
                                                     "/Volumes/" + 
                                                     str(volume_id))
                    subvolume_key = cluster_key + "/Volumes/" + str(volume_id)
                    subvolume_details = get_subvolume_details(subvolume_key)
                    for volume in volume_details.leaves:
                        try:
	                    if volume.key.rsplit('/')[-1] in attrs["volumes"]:
                                volume_data[volume.key.rsplit('/')[-1]] = volume.value
                        except (KeyError, etcd.EtcdKeyNotFound) as ex:
                                logger.log("error", NS.get("publisher_id", None),
                                          {'message': "Error while fetching volume_details" + str(ex)})
                    volume_data["subvolume"] = subvolume_details
                    cluster_obj.volumes.append(volume_data)
                except (KeyError, etcd.EtcdKeyNotFound) as ex:
                        logger.log("error", NS.get("publisher_id", None),
                                   {'message': "Error while fetching volume id {}".format(volume_id) + str(ex)})
            for bricks in cluster_obj.bricks:
                for volume in cluster_obj.volumes:
                    try:
                        if volume["vol_id"] == bricks["vol_id"]:
                            bricks["vol_name"] = volume["name"]
                    except (KeyError, etcd.EtcdKeyNotFound) as ex:
                        logger.log("error", NS.get("publisher_id", None),
                                   {'message': "Error while getting volumelevel brick details" + str(ex)})
            cluster_details_list.append(cluster_obj)
        return cluster_details_list
    except (etcd.EtcdKeyNotFound, KeyError) as ex:
        logger.log("error", NS.get("publisher_id", None),
                  {'message': str(ex)})
        return None


def set_alert(panel, alert_thresholds, panel_title, resource_name):
    panel["thresholds"] = [{"colorMode": "critical", "fill": True, "line": True,
                            "op": "gt", "value": alert_thresholds[panel_title]["Warning"]}]

    panel["alert"] = {"conditions": [{"evaluator": {"params": [alert_thresholds[panel_title]["Warning"]], "type": "gt"},
                                      "operator": {"type": "and"},
                                      "query": {"params": [panel["targets"][-1]["refId"],"3m","now"]},
                                      "reducer": {"params": [], "type": "avg" },
                                      "type": "query"}],
                                      "executionErrorState": "keep_state", "frequency": "60s", "handler": 1,
                                      "name": str(resource_name) + " " + str(panel["title"]) + " Alert", "noDataState": "keep_state",
                                      "notifications": []}



def get_resource_list(cluster_detail, resource_type):

    resource = []
    if resource_type == "volumes":
        for volume in cluster_detail.volumes:
            resource.append(volume)
        return resource
    if resource_type == "hosts":
        for host in cluster_detail.hosts:
            resource.append(host)
        return resource
    if resource_type == "bricks":
        for brick in cluster_detail.bricks:
            resource.append(brick)
        return resource
    if resource_type == "clusters":
        resource.append(cluster_detail.integration_id)
        return resource
    return None


def get_rows(resource_rows):

    new_resource_rows = []
    try:
        for row in resource_rows:
            panels = row["panels"]
            for panel in panels:
                if panel["type"] == "graph":
                    row["panels"] = [panel]
                    new_resource_rows.append(copy.deepcopy(row))
    except (KeyError, AttributeError) as ex:
        logger.log("error", NS.get("publisher_id", None),
                  {'message': "Error in retrieving resource rows (get_rows) " +
                   str(ex)})
    return new_resource_rows


def set_target(target, cluster_detail, resource, resource_name):

    target["target"] = target["target"].replace('$interval', '1m')
    target["target"] = target["target"].replace('$my_app', 'tendrl')
    target["target"] = target["target"].replace('$cluster_id',
                                                str(cluster_detail.integration_id))
    if resource_name == "volumes":
        target["target"]= target["target"].replace('$volume_name',
                                                   str(resource["name"]))
        new_title = str(resource["name"])
    elif resource_name == "hosts":
        target["target"]= target["target"].replace('$host_name',
                                                   str(resource["fq" + \
                                                   "dn"].replace(".", "_")))
        new_title = str(resource["fqdn"].replace(".", "_"))
    elif resource_name == "bricks":
        target["target"]= target["target"].replace('$host_name',
                                                   str(resource["host" + \
                                                   "name"].replace(".", "_")))
        target["target"]= target["target"].replace('$brick_path',
                                                   str(resource["brick_path"]))
        target["target"]= target["target"].replace('$volume_name',
                                                   str(resource["vol_name"]))
        new_title = str(resource["vol_name"] + "-" + resource["hostname"].replace(".", "_")) + \
                    "-" + str(resource["brick_path"])
    if "alias" in target["target"] and "aliasByNode" not in target["target"] :
        target["target"] = target["target"].split('(',1)[-1].rsplit(',', 1)[0]
    return new_title


def create_resource_dashboard(cluster_details_list, resource_name):

    if resource_name == "clusters":
        dashboard_path = '/etc/tendrl/monitoring-integration' + \
                         '/grafana/dashboards/' + \
                         'tendrl-gluster-at-a-glance.json'
    else:
        dashboard_path = '/etc/tendrl/monitoring-integration' + \
                         '/grafana/dashboards/' + \
                         'tendrl-gluster-' + str(resource_name) +'.json'

    if os.path.exists(dashboard_path):
        resource_file = utils.fread(dashboard_path)
        try:
            resource_json = json.loads(resource_file)
            resource_json["dashboard"]["title"] = "Alerts - " + \
                str(resource_json["dashboard"]["title"])
            resource_rows = resource_json["dashboard"]["rows"]
            global_row = { "collapse":False,
                           "height":250,
                           "panels":[],
                           "repeat":"null",
                           "repeatIteration":"null",
                           "repeatRowId":"null",
                           "showTitle":False,
                           "title":"Dashboard Row",
                           "titleSize":"h6"
                         }
            new_resource_rows = get_rows(resource_rows)
            alert_thresholds = NS.monitoring.definitions.get_parsed_defs()["namespace.monitoring"]["thresholds"][resource_name]
            all_resource_rows = []
            count = 1
            for cluster_detail in cluster_details_list:
                resources = get_resource_list(cluster_detail, resource_name)
                for resource in resources:
                    global_row["panels"] = []
                    panel_count = 1
                    for row in new_resource_rows:
                        new_row = copy.deepcopy(row)
                        panels = new_row["panels"]
                        new_title = ""
                        for panel in panels:
                            try:
                                flag = False
                                for panel_title in alert_thresholds:
                                    if not panel["title"].lower().find(panel_title.replace("_", " ")):
                                        targets  = panel["targets"]
                                        for target in targets:
                                            new_title = set_target(target, cluster_detail, resource, resource_name)
                                        set_alert(panel, alert_thresholds, panel_title, resource_name)
                                        panel["id"] = count
                                        panel["legend"]["show"] = False
                                        panel["title"] = panel["title"] + " - " + str(new_title)
                                        count = count + 1
                                        panel_count = panel_count + 1
                                        if panel_count < 7:
                                            global_row["panels"].append(panel)
                                        else:
                                            global_row["panels"].append(panel)
                                            all_resource_rows.append(copy.deepcopy(global_row))
                                            global_row["panels"] = []
                                            panel_count = 1
                            except KeyError as ex:
                                logger.log("error", NS.get("publisher_id", None),
                                           {'message': str(panel["title"]) + "failed" + str(ex)})
                    all_resource_rows.append(copy.deepcopy(global_row))

            resource_json["dashboard"]["rows"] = []
            resource_json["dashboard"]["rows"] = all_resource_rows
            resource_json["dashboard"]["templating"] = {}
            return resource_json
        except Exception as ex:
            logger.log("error", NS.get("publisher_id", None),
                      {'message': str(ex)})
            return None


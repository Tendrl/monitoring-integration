import copy
import json
import sys


import etcd
import maps


from tendrl.monitoring_integration.grafana import cluster_details
from cluster_details import ClusterDetails
from tendrl.commons.utils import etcd_utils

# TODO(Rishubh) Fetch alert details like threshold from config file

def get_cluster_details():

    ''' 
        To get details of glusters from etcd
        TODO: Optimize the code, reduce number of etcd calls 
        TODO: Extract etcd host and port from configuration file '''

    cluster_details_list = []
    try:
        result = etcd_utils.read('/clusters')
        for item in result.leaves:
            cluster_obj = ClusterDetails()
            cluster_obj.cluster_id =  item.key.split('/')[-1]
            client_str = '/clusters/' + str(cluster_obj.cluster_id)
            cluster_details = etcd_utils.read(client_str)
            for cluster in cluster_details.leaves:
                if 'Volumes' in cluster.key:
                    volumes = etcd_utils.read(client_str + "/Volumes")
                    for volume in volumes.leaves:
                        volume_id =  volume.key.split('/')[-1]
                        volume_details = etcd_utils.read(client_str + "/Volumes/" + str(volume_id))
                        vol_dict = maps.NamedDict()
                        for vol in volume_details.leaves:
                            if "name" in vol.key:
                                vol_dict.volume_name = vol.value
                            if "Bricks" in vol.key:
                                subvolume_details = etcd_utils.read(client_str + "/Volumes/" + str(volume_id)+ "/Bricks")
                                vol_dict.bricks = []
                                for subvolume in subvolume_details.leaves:
                                   brick_details = etcd_utils.read(client_str + "/Volumes/" + str(volume_id)+ "/Bricks/" + str(subvolume.key.split('/')[-1]))
                                   for brick in brick_details.leaves:
                                       vol_dict.bricks.append(brick.key.split('/')[-1])
                        cluster_obj.volumes.append(vol_dict)
                if 'nodes' in cluster.key:
                   nodes = etcd_utils.read(client_str + "/nodes")
                   for node in nodes.leaves:
                        node_id = node.key.split('/')[-1]
                        node_details = etcd_utils.read(client_str + "/nodes/" + str(node_id) + "/NodeContext")
                        for row in node_details.leaves:
                            if "fqdn" in row.key:
                                cluster_obj.hosts.append(row.value)

            cluster_details_list.append(cluster_obj)
        return cluster_details_list
    except etcd.EtcdKeyNotFound as ex:
        sys.stdout.write("Etcd Key Not Found" + str(ex))
    return None

def set_alert():

    panel["thresholds"] = [{"colorMode": "critical","fill": True,"line": True,"op": "gt","value": 1}]
    panel["alert"] = {"conditions": [{"evaluator": {"params": [2],"type": "gt"},
                                      "operator": {"type": "and"},"query": {"params": ["A","5m","now"] },
                                      "reducer": {"params": [],"type": "avg" },"type": "query"}],
                                      "executionErrorState": "alerting","frequency": "6s","handler": 1,
                                      "name": str(panel["title"]) + " Alert","noDataState": "no_data","notifications": []}

def create_volume_dashboard(cluster_details_list):

    volume_file =  open('/etc/tendrl/monitoring-integration/grafana/dashboards/tendrl-gluster-volumes.json')
    volume_json = json.load(volume_file)
    volume_json["dashboard"]["title"] = "Alerts - " + str(volume_json["dashboard"]["title"])
    volume_rows = volume_json["dashboard"]["rows"]
    new_volume_rows = []
    for row in volume_rows:
        panels = row["panels"]
        for panel in panels:
            if panel["type"] == "graph":
               row["panels"] = [panel]
               new_volume_rows.append(copy.deepcopy(row))

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

    all_volume_rows = []

    count = 1
    for cluster_detail in cluster_details_list:
        for volume in cluster_detail.volumes:
            global_row["panels"] = []
            panel_count = 1
            for row in new_volume_rows:
                new_row = copy.deepcopy(row)
                panels = new_row["panels"]
                for panel in panels:
                    targets  = panel["targets"]
                    for target in targets:
                        target["target"] = target["target"].replace('$interval','1m')
                        target["target"] = target["target"].replace('$my_app','tendrl')
                        target["target"] = target["target"].replace('$cluster_id',str(cluster_detail.cluster_id))
                        target["target"] = target["target"].replace('$volume_name',str(volume.volume_name))
                        if "alias" in target["target"]:
                            target["target"] = target["target"].split('(',1)[-1].split(',')[0]
                    set_alert(panel)
                    panel["id"] = count
                    panel["title"] = panel["title"] + " - " + str(volume.volume_name)
                    panel["span"] = 2
                    panel["legend"]["show"] = False
                    count = count + 1
                    panel_count = panel_count + 1
                    if panel_count < 7:
                        global_row["panels"].append(panel)
                    else:
                        global_row["panels"].append(panel)
                        all_host_rows.append(copy.deepcopy(global_row))
                        global_row["panels"] = []
                        panel_count = 1
            all_volume_rows.append(copy.deepcopy(global_row))

    volume_json["dashboard"]["rows"] = all_volume_rows
    volume_json["dashboard"]["templating"] = {}
    return json.dumps(volume_json)


def create_host_dashboard(cluster_details_list):

    host_file =  open('/etc/tendrl/monitoring-integration/grafana/dashboards/tendrl-gluster-hosts.json')
    host_json = json.load(host_file)
    host_json["dashboard"]["title"] = "Alerts - " + str(host_json["dashboard"]["title"])
    host_rows = host_json["dashboard"]["rows"]
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
    new_host_rows = []
    for row in host_rows:
        panels = copy.deepcopy(row["panels"])
        for panel in panels:
            if panel["type"] == "graph":
               row["panels"] = [panel]
               new_host_rows.append(copy.deepcopy(row))

    all_host_rows = []
    count = 1
    for cluster_detail in cluster_details_list:
        for host in cluster_detail.hosts:
            global_row["panels"] = []
            panel_count = 1
            for row in new_host_rows:
                new_row = copy.deepcopy(row)
                panels = new_row["panels"]
                for panel in panels:
                    targets  = panel["targets"]
                    for target in targets:
                        target["target"] = target["target"].replace('$interval','1m')
                        target["target"] = target["target"].replace('$my_app','tendrl')
                        target["target"] = target["target"].replace('$cluster_id',str(cluster_detail.cluster_id))
                        target["target"]= target["target"].replace('$host_name',str(host).replace('.','_'))
                        if "alias" in target["target"]:
                            target["target"] = target["target"].split('(',1)[-1].split(',')[0]
                    set_alert(panel)
                    panel["id"] = count
                    panel["title"] = panel["title"] + " - " + str(host).replace('.','_')
                    panel["span"] = 2
                    panel["legend"]["show"] = False
                    count = count + 1
                    panel_count = panel_count + 1
                    if panel_count < 7:
                        global_row["panels"].append(panel)
                    else:
                        global_row["panels"].append(panel)
                        all_host_rows.append(copy.deepcopy(global_row))
                        global_row["panels"] = []
                        panel_count = 1
            all_host_rows.append(copy.deepcopy(global_row))

    host_json["dashboard"]["rows"] = []
    host_json["dashboard"]["rows"] = all_host_rows
    host_json["dashboard"]["templating"] = {}
    return json.dumps(host_json)


def create_brick_dashboard(cluster_details_list):


    brick_file =  open('/etc/tendrl/monitoring-integration/grafana/dashboards/tendrl-gluster-bricks.json')
    brick_json = json.load(brick_file)
    brick_json["dashboard"]["title"] = "Alerts - " + str(brick_json["dashboard"]["title"])
    brick_rows = brick_json["dashboard"]["rows"]
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
    new_brick_rows = []
    for row in brick_rows:
        panels = row["panels"]
        for panel in panels:
            if panel["type"] == "graph":
                row["panels"] = [panel]
                new_brick_rows.append(copy.deepcopy(row))

    all_brick_rows = []
    count = 1
    for cluster_detail in cluster_details_list:
        for volume in cluster_detail.volumes:
            for brick in volume.bricks:
                global_row["panels"] = []
                panel_count = 1
                for row in new_brick_rows:
                    new_row = copy.deepcopy(row)
                    panels = new_row["panels"]
                    for panel in panels:
                        targets  = panel["targets"]
                        for target in targets:
                            target["target"] = target["target"].replace('$interval','1m')
                            target["target"] = target["target"].replace('$my_app','tendrl')
                            target["target"] = target["target"].replace('$cluster_id',str(cluster_detail.cluster_id))
                            target["target"]= target["target"].replace('$volume_name',str(volume.volume_name))
                            target["target"]= target["target"].replace('$brick_name',str(brick).split(':')[-1].replace('_','|',2))
                            if "alias" in target["target"]:
                                target["target"] = target["target"].split('(',1)[-1].split(',')[0]
                        set_alert(panel)
                        panel["id"] = count
                        panel["legend"]["show"] = False
                        panel["title"] = panel["title"] + " - " + str(brick).replace('.','_')
                        count = count + 1
                        panel_count = panel_count + 1
                        if panel_count < 7:
                            global_row["panels"].append(panel)
                        else:
                            global_row["panels"].append(panel)
                            all_brick_rows.append(copy.deepcopy(global_row))
                            global_row["panels"] = []
                            panel_count = 1
                all_brick_rows.append(copy.deepcopy(global_row))

    brick_json["dashboard"]["rows"] = []
    brick_json["dashboard"]["rows"] = all_brick_rows
    brick_json["dashboard"]["templating"] = {}
    return json.dumps(brick_json)


def create_gluster_at_a_glance_dashboard(cluster_details_list):

    cluster_file =  open('/etc/tendrl/monitoring-integration/grafana/dashboards/tendrl-gluster-at-a-glance.json')
    cluster_json = json.load(cluster_file)
    cluster_json["dashboard"]["title"] = "Alerts - " + str(cluster_json["dashboard"]["title"])
    cluster_rows = cluster_json["dashboard"]["rows"]
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
    new_cluster_rows = []
    for row in cluster_rows:
        panels = row["panels"]
        for panel in panels:
            if panel["type"] == "graph":
                row["panels"] = [panel]
                new_cluster_rows.append(copy.deepcopy(row))

    all_cluster_rows = []
    count = 1
    for cluster_detail in cluster_details_list:
        global_row["panels"] = []
        panel_count = 1
        for row in new_brick_rows:
            new_row = copy.deepcopy(row)
            panels = new_row["panels"]
            for panel in panels:
                targets  = panel["targets"]
                for target in targets:
                    target["target"] = target["target"].replace('$interval','1m')
                    target["target"] = target["target"].replace('$my_app','tendrl')
                    target["target"] = target["target"].replace('$cluster_id',str(cluster_detail.cluster_id))
                    if "alias" in target["target"]:
                        target["target"] = target["target"].split('(',1)[-1].split(',')[0]
                set_alert(panel)
                panel["id"] = count
                panel["title"] = panel["title"] + " - " + str(cluster_detail.cluster_id)
                panel["legend"]["show"] = False
                count = count + 1
                panel_count = panel_count + 1
                if panel_count < 7:
                    global_row["panels"].append(panel)
                else:
                    global_row["panels"].append(panel)
                    all_cluster_rows.append(copy.deepcopy(global_row))
                    global_row["panels"] = []
                    panel_count = 1
        all_cluster_rows.append(copy.deepcopy(global_row))

    cluster_json["dashboard"]["rows"] = []
    cluster_json["dashboard"]["rows"] = all_cluster_rows
    cluster_json["dashboard"]["templating"] = {}
    return json.dumps(cluster_json)

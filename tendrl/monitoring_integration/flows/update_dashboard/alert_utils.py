import copy
import json

from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.grafana.grafana_org_utils import  \
    get_current_org_name
from tendrl.monitoring_integration.grafana import grafana_org_utils


def get_alert_dashboard(dashboard_name):
    if dashboard_name == "nodes":
        slug = "alerts-tendrl-gluster-hosts"
    else:
        slug = "alerts-tendrl-gluster-" + str(dashboard_name)
    dashboard_json = {}
    if get_current_org_name()["name"] == "Alert_dashboard":
        dashboard_json = dashboard.get_dashboard(slug)
    elif switch_context("Alert_dashboard"):
        dashboard_json = dashboard.get_dashboard(slug)
        # return to main org
        switch_context("Main Org.")
    return dashboard_json


def delete_alert_dashboard(dashboard_name):
    if dashboard_name == "nodes":
        slug = "alerts-tendrl-gluster-hosts"
    else:
        slug = "alerts-tendrl-gluster-" + str(dashboard_name)
    dashboard_json = {}
    if get_current_org_name()["name"] == "Alert_dashboard":
        dashboard_json = dashboard.delete_dashboard(slug)
    elif switch_context("Alert_dashboard"):
        dashboard_json = dashboard.delete_dashboard(slug)
        # return to main org
        switch_context("Main Org.")
    return dashboard_json


def fetch_row(dashboard_json):

    rows = dashboard_json["dashboard"]["rows"]
    if len(rows) > 1:
        for count in xrange(1, len(rows)):
            if rows[0]["panels"][0]["title"].split("-", 1)[0] == \
                    rows[count]["panels"][0]["title"].split("-", 1)[0]:
                alert_row = copy.deepcopy(
                    dashboard_json["dashboard"]["rows"][-count:])
                break
    else:
        alert_row = [copy.deepcopy(dashboard_json["dashboard"]["rows"][-1])]
    return alert_row


def add_resource_panel(alert_rows, cluster_id, resource_type, resource_name):

    for alert_row in alert_rows:
        panel_count = alert_row["panels"][-1]["id"] + 1
        for panel in alert_row["panels"]:
            targets = panel["targets"]
            for target in targets:
                try:
                    if resource_type == "bricks":
                        panel_target = ("tendrl" + target["target"].split(
                            "tendrl")[1].split(")")[0]).split(".")
                        old_cluster_id = panel_target[
                            panel_target.index("clusters") + 1]
                        target["target"] = target["target"].replace(
                            old_cluster_id, str(cluster_id))
                        if "volumes" in panel_target:
                            old_resource_name = panel_target[
                                panel_target.index("volumes") + 1]
                            target["target"] = target["target"].replace(
                                old_resource_name,
                                str(resource_name.split("|", 1)[0]))
                        if "nodes" in panel_target:
                            old_resource_name = panel_target[
                                panel_target.index("nodes") + 1]
                            target["target"] = target["target"].replace(
                                old_resource_name,
                                str(resource_name.split("|", 1)[1].split(
                                    ":", 1)[0].replace(".", "_")))
                        if "bricks" in panel_target:
                            old_resource_name = panel_target[
                                panel_target.index("bricks") + 1]
                            target["target"] = target["target"].replace(
                                old_resource_name,
                                str(resource_name.split("|", 1)[1].split(
                                    ":", 1)[1].replace("/", "|")))
                    else:
                        panel_target = ("tendrl" + target["target"].split(
                            "tendrl")[1].split(")")[0]).split(".")
                        old_cluster_id = panel_target[
                            panel_target.index("clusters") + 1]
                        target["target"] = target["target"].replace(
                            old_cluster_id, str(cluster_id))
                        if resource_name is not None:
                            old_resource_name = panel_target[
                                panel_target.index(str(resource_type)) + 1]
                            target["target"] = target["target"].replace(
                                old_resource_name, str(resource_name))
                except (KeyError, IndexError):
                    pass
            panel["id"] = panel_count
            panel_count = panel_count + 1
            new_title = resource_name
            if resource_type == "bricks":
                host_name = resourcename.split("|", 1)[1].split(
                    ":", 1)[0].replace(".", "")
                brick_name = resource_name.split("|", 1)[1].split(
                    ":", 1)[1].replace("/", "|")
                volume_name = resource_name.split("|",1)[0]
                new_title = volume_name + "|" + host_name + ":" + brick_name
            panel["title"] = panel["title"].split(
                "-", 1)[0] + "-" + str(new_title)


def remove_row(alert_dashboard, cluster_id, resource_type, resource_name):

    rows = alert_dashboard["dashboard"]["rows"]
    new_rows = []
    flag = True
    for row in rows:
        for target in row["panels"][0]["targets"]:
            resource = resource_name
            if resource_type == "bricks":
                hostname = resource.split(":")[0].split("|")[1].replace(".", "_")
                resource = "." + resource.split(
                    ":", 1)[1].replace("/", "|") + "."
            if resource is not None:
                if str(cluster_id) in target["target"] and str(
                        resource) in target["target"]:
                    if resource_type == "bricks":
                        if hostname in target["target"]:
                            flag = False
                            break
                    else:
                        flag = False
                        break
            else:
                if str(cluster_id) in target["target"]:
                    flag = False
                    break
        if flag:
            new_rows.append(row)
        flag = True
    alert_dashboard["dashboard"]["rows"] = new_rows


def remove_cluster_rows(cluster_id, dashboard_name):

    alert_dashboard = get_alert_dashboard(dashboard_name)
    new_rows = []
    flag = True
    rows = alert_dashboard["dashboard"]["rows"]
    for row in rows:
        for target in row["panels"][0]["targets"]:
            if str(cluster_id) in target["target"]:
                flag = False
                break
        if flag:
            new_rows.append(row)
        flag = True
    alert_dashboard["dashboard"]["rows"] = new_rows
    return alert_dashboard


def create_updated_dashboard(dashboard_json, alert_rows):
    dashboard_json["dashboard"]["rows"] = dashboard_json[
        "dashboard"]["rows"] + alert_rows
    return dashboard_json


def switch_context(org_name):
    alert_org_id = grafana_org_utils.get_org_id(
        org_name
    )
    switched = grafana_org_utils.switch_context(json.loads(
        alert_org_id)["id"]
    ) 
    return switched

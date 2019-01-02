import json
import re

from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import constants
from tendrl.monitoring_integration.grafana import dashboard_utils
from tendrl.monitoring_integration.grafana import grafana_org_utils

GLUSTER_DASHBOARDS = {
    "host": "nodes",
    "volume": "volumes",
    "brick": "bricks"
}


def get_alert_dashboard(dashboard_name):
    if dashboard_name == "nodes":
        slug = "alerts-host-dashboard"
    else:
        slug = "alerts-" + str(dashboard_name)[:-1] + "-dashboard"
    dashboard_json = {}
    if grafana_org_utils.get_current_org_name()["name"] == \
            constants.ALERT_ORG:
        dashboard_json = dashboard_utils.get_dashboard(slug)
    elif switch_context(constants.ALERT_ORG):
        dashboard_json = dashboard_utils.get_dashboard(slug)
        # return to main org
        switch_context(constants.MAIN_ORG)
    return dashboard_json


def switch_context(org_name):
    alert_org_id = grafana_org_utils.get_org_id(
        org_name
    )
    switched = grafana_org_utils.switch_context(json.loads(
        alert_org_id)["id"]
    )
    return switched


def delete_alert_dashboard(dashboard_name):
    slug = "alerts-" + str(dashboard_name)[:-1] + "-dashboard"
    dashboard_json = {}
    if grafana_org_utils.get_current_org_name()["name"] == \
            constants.ALERT_ORG:
        dashboard_json = dashboard_utils.delete_dashboard(slug)
    elif switch_context(constants.ALERT_ORG):
        dashboard_json = dashboard_utils.delete_dashboard(slug)
        # return to main org
        switch_context(constants.MAIN_ORG)
    return dashboard_json


def post_dashboard(alert_dashboard):
    resp = None
    if grafana_org_utils.get_current_org_name()["name"] == \
            constants.ALERT_ORG:
        resp = dashboard_utils._post_dashboard(alert_dashboard)
    elif switch_context(constants.ALERT_ORG):
        resp = dashboard_utils._post_dashboard(alert_dashboard)
        # return to main org
        switch_context(constants.MAIN_ORG)
    return resp


def get_alert(alert_id):
    resp = None
    if grafana_org_utils.get_current_org_name()["name"] == \
            constants.ALERT_ORG:
        resp = dashboard_utils.get_alert(alert_id)
    elif switch_context(constants.ALERT_ORG):
        resp = dashboard_utils.get_alert(alert_id)
        # return to main org
        switch_context(constants.MAIN_ORG)
    return resp.json()


def remove_row(alert_dashboard, integration_id, resource_type, resource_name):
    rows = alert_dashboard["dashboard"]["rows"]
    new_rows = []
    flag = True
    for row in rows:
        for target in row["panels"][0]["targets"]:
            if resource_type == "bricks":
                result = parse_target(
                    target['target'],
                    constants.BRICK_TEMPLATE
                )
                hostname = resource_name.split(":")[0].split(
                    "|")[1].replace(".", "_")
                brick_path = resource_name.split(
                    ":", 1)[1].replace("/", constants.BRICK_PATH_SEPARATOR)
                if result['integration_id'] == integration_id and \
                        hostname == result["host_name"] and \
                        brick_path == result["brick_path"]:
                    flag = False
                    break
            elif resource_type == "nodes":
                result = parse_target(
                    target['target'],
                    constants.HOST_TEMPLATE
                )
                if result['integration_id'] == integration_id and \
                        resource_name == result["host_name"]:
                    flag = False
                    break
            elif resource_type == "volumes":
                result = parse_target(
                    target['target'],
                    constants.VOLUME_TEMPLATE
                )
                if resource_name == result["volume_name"]:
                    flag = False
                    break
        if flag:
            new_rows.append(row)
        flag = True
    alert_dashboard["dashboard"]["rows"] = new_rows


def remove_cluster_rows(integration_id, dashboard_name):
    alert_dashboard = get_alert_dashboard(dashboard_name)
    if 'message' in alert_dashboard and \
            'Dashboard not found' in alert_dashboard["message"]:
        return

    new_rows = []
    flag = True
    rows = alert_dashboard.get("dashboard", {}).get("rows", [])
    for row in rows:
        for target in row["panels"][0].get("targets", []):
            if str(integration_id) in target["target"]:
                flag = False
                break
        if flag:
            new_rows.append(row)
        flag = True
    alert_dashboard["dashboard"]["rows"] = new_rows
    return alert_dashboard


def delete_panel(
    integration_id, resource_type=None, resource_name=None
):
    if resource_name is None:
        # delete all dashboards using integration id
        for dash_name in GLUSTER_DASHBOARDS:
            alert_dashboard = remove_cluster_rows(
                integration_id,
                GLUSTER_DASHBOARDS[dash_name]
            )
            resp = post_dashboard(alert_dashboard)
            if resp.status_code != 200:
                logger.log(
                    "debug",
                    NS.publisher_id,
                    {
                        "message": "Failed to remove %s alert dashboard "
                        "(integration_id: %s)" % (dash_name, integration_id)
                    }
                )
    else:
        if resource_type == "nodes":
            resource_name = resource_name.replace(".", "_")
        alert_dashboard = get_alert_dashboard(resource_type)
        remove_row(
            alert_dashboard,
            integration_id,
            resource_type,
            resource_name
        )
        resp = post_dashboard(alert_dashboard)
    return resp


def parse_target(target, template):
    regex = re.sub(r'{(.+?)}', r'(?P<\1>.+?)', template)
    values = list(re.search(regex, target).groups())
    keys = re.findall(r'{(.+?)}', template)
    _dict = dict(zip(keys, values))
    return _dict

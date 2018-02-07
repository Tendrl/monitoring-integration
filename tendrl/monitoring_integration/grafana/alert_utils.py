import json

from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.grafana import grafana_org_utils


ALERT_ORG = "Alert_dashboard"
MAIN_ORG = "Main Org."


def get_alert_dashboard(dashboard_name):
    if dashboard_name == "nodes":
        slug = "alerts-tendrl-gluster-hosts"
    else:
        slug = "alerts-tendrl-gluster-" + str(dashboard_name)
    dashboard_json = {}
    if grafana_org_utils.get_current_org_name()["name"] == \
            ALERT_ORG:
        dashboard_json = dashboard.get_dashboard(slug)
    elif switch_context(ALERT_ORG):
        dashboard_json = dashboard.get_dashboard(slug)
        # return to main org
        switch_context(MAIN_ORG)
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
    slug = "alerts-tendrl-gluster-" + str(dashboard_name)
    dashboard_json = {}
    if grafana_org_utils.get_current_org_name()["name"] == \
            ALERT_ORG:
        dashboard_json = dashboard.delete_dashboard(slug)
    elif switch_context(ALERT_ORG):
        dashboard_json = dashboard.delete_dashboard(slug)
        # return to main org
        switch_context(MAIN_ORG)
    return dashboard_json


def post_dashboard(alert_dashboard):
        resp = None
        if grafana_org_utils.get_current_org_name()["name"] == ALERT_ORG:
            resp = dashboard._post_dashboard(alert_dashboard)
        elif switch_context(ALERT_ORG):
            resp = dashboard._post_dashboard(alert_dashboard)
            # return to main org
            switch_context(MAIN_ORG)
        return resp

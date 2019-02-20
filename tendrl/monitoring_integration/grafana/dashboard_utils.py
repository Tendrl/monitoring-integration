import json
import maps
import os
import traceback

from requests import delete
from requests import get
from requests import post
from requests import put

from tendrl.monitoring_integration.grafana import constants
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import utils


def _post_dashboard(dashboard_json, authorization_key=None):
    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        upload_str = json.dumps(dashboard_json)
        if authorization_key:
            new_header = constants.HEADERS
            new_header["Authorization"] = "Bearer " + str(authorization_key)
            response = post("http://{}:{}/api/dashboards/"
                            "db".format(
                                config.grafana_host,
                                config.grafana_port
                            ),
                            headers=new_header,
                            data=upload_str)
        else:
            response = post("http://{}:{}/api/dashboards/"
                            "db".format(
                                config.grafana_host,
                                config.grafana_port
                            ),
                            headers=constants.HEADERS,
                            auth=config.credentials,
                            data=upload_str)
        return response
    else:
        raise exceptions.ConnectionFailedException


def get_dashboard(dashboard_name):
    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        resp = get("http://{}:{}/api/dashboards/"
                   "db/{}".format(config.grafana_host,
                                  config.grafana_port,
                                  dashboard_name),
                   auth=config.credentials)
    else:
        raise exceptions.ConnectionFailedException
    return resp.json()


def delete_dashboard(dashboard_name):
    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        resp = delete(
            "http://{}:{}/api/dashboards/db/{}".format(
                config.grafana_host,
                config.grafana_port,
                dashboard_name
            ),
            auth=config.credentials
        )
    else:
        raise exceptions.ConnectionFailedException
    return resp.json()


def get_all_dashboards():
    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        resp = get("http://{}:{}/api/search/"
                   .format(config.grafana_host, config.grafana_port),
                   auth=config.credentials)
    else:
        raise exceptions.ConnectionFailedException
    return resp.json()


def set_home_dashboard(dash_id):
    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        resp = put('http://{}:{}/api/org/'
                   'preferences'.format(
                       config.grafana_host,
                       config.grafana_port
                   ),
                   headers=constants.HEADERS,
                   auth=config.credentials,
                   data=json.dumps({"name": constants.MAIN_ORG,
                                    "theme": "light",
                                    "homeDashboardId": dash_id}))
    else:
        raise exceptions.ConnectionFailedException
    return resp


def create_dashboard(dashboard_name, dashboard_dir=None):
    if not dashboard_dir:
        dashboard_dir = "/etc/tendrl/monitoring-integration/grafana/dashboards"
    dashboard_path = os.path.join(dashboard_dir,
                                  "{}.json".format(dashboard_name))

    if os.path.exists(dashboard_path):

        dashboard_data = utils.fread(dashboard_path)

        try:
            dashboard_json = json.loads(dashboard_data)
            response = _post_dashboard(dashboard_json)
            return response

        except exceptions.ConnectionFailedException:
            traceback.print_stack()
            raise exceptions.ConnectionFailedException

    else:
        raise exceptions.FileNotFoundException


def get_alert(alert_id):
    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        resp = get(
            "http://{}:{}/api/alerts/{}".format(
                config.grafana_host,
                config.grafana_port,
                alert_id
            ),
            auth=config["credentials"]
        )
    else:
        raise exceptions.ConnectionFailedException
    return resp

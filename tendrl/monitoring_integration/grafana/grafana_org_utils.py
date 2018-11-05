import json
import maps

from requests import get
from requests import post

from tendrl.monitoring_integration.grafana import constants
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import utils


def create_org(org_name):

    config = maps.NamedDict(NS.config.data)
    upload_str = {"name": org_name}
    if utils.port_open(config.grafana_port, config.grafana_host):
        response = post(
            "http://{}/grafana/api/orgs".format(
                config.grafana_host
            ),
            headers=constants.HEADERS,
            auth=config.credentials,
            data=json.dumps(upload_str)
        )
        try:
            return json.loads(response.content)["orgId"]
        except KeyError:
            return None
    else:
        raise exceptions.ConnectionFailedException


def get_org_id(org_name):

    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        resp = get(
            "http://{}/grafana/api/orgs/name/{}".format(
                config.grafana_host,
                org_name
            ),
            auth=config.credentials
        )
        try:
            return resp.content
        except (KeyError, AttributeError):
            return None
    else:
        raise exceptions.ConnectionFailedException


def get_current_org_name():
    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        resp = get(
            "http://{}/grafana/api/org/".format(
                config.grafana_host
            ),
            auth=config.credentials
        )
        try:
            return resp.json()
        except (KeyError, AttributeError):
            return None
    else:
        raise exceptions.ConnectionFailedException


def switch_context(org_id):
    config = maps.NamedDict(NS.config.data)
    upload_str = ''
    if utils.port_open(config.grafana_port, config.grafana_host):
        response = post("http://{}/grafana/api/user/using"
                        "/{}".format(config.grafana_host,
                                     org_id),
                        headers=constants.HEADERS,
                        auth=config.credentials,
                        data=upload_str)
        try:
            if "changed" in json.loads(response.content)["message"]:
                return True
            else:
                return False
        except KeyError:
            return False
    else:
        raise exceptions.ConnectionFailedException


def create_api_token(key_name, role):
    config = maps.NamedDict(NS.config.data)
    request_body = {"name": key_name, "role": role}
    if utils.port_open(config.grafana_port, config.grafana_host):
        response = post("http://{}/grafana/api/auth/"
                        "keys".format(config.grafana_host),
                        headers=constants.HEADERS,
                        auth=config.credentials,
                        data=json.dumps(request_body))
        try:
            return json.loads(response.content)["key"]
        except KeyError:
            return None


def get_auth_keys():
    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        response = get(
            "http://{}/grafana/api/auth/keys".format(
                config.grafana_host
            ),
            auth=config.credentials
        )
        try:
            return json.loads(response.content)
        except KeyError:
            return None

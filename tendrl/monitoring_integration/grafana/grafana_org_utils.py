import __builtin__
import json


from requests import post
import maps


from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration.grafana import exceptions


HEADERS = {"Accept": "application/json",
           "Content-Type": "application/json"
           }


''' Create new organisation'''

def create_org(org_name):

    config = maps.NamedDict(NS.config.data)
    upload_str = {"name":org_name}
    if utils.port_open(config.grafana_port, config.grafana_host):
        response = post("http://{}:{}/api/orgs".format(config.grafana_host,
                                                       config.grafana_port),
                        headers=HEADERS,
                        auth=config.credentials,
                        data=json.dumps(upload_str))
        try:
            return json.loads(response._content)["orgId"] 
        except KeyError as ex:
            return None
    else:
        raise exceptions.ConnectionFailedException


''' Switch context to particular org '''

def switch_context(org_id):
    config = maps.NamedDict(NS.config.data)
    upload_str = ''
    if utils.port_open(config.grafana_port, config.grafana_host):
        response = post("http://{}:{}/api/user/using/{}".format(config.grafana_host,
                                                                config.grafana_port,
                                                                org_id),
                        headers=HEADERS,
                        auth=config.credentials,
                        data=upload_str)
  
        try:
            if "changed" in json.loads(response._content)["message"]:
                return True
            else:
                return False
        except KeyError as ex:
            return False
    else:
        raise exceptions.ConnectionFailedException


def create_api_token(key_name, role):
    config = maps.NamedDict(NS.config.data)
    request_body = {"name": key_name, "role": role}
    if utils.port_open(config.grafana_port, config.grafana_host):
        response = post("http://{}:{}/api/auth/keys".format(config.grafana_host,
                                                            config.grafana_port),
                        headers=HEADERS,
                        auth=config.credentials,
                        data=json.dumps(request_body))
        try:
            return json.loads(response._content)["key"]
        except KeyError as ex:
            return None

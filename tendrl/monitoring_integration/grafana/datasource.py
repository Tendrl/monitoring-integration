import __builtin__
import json
import traceback


from requests import post


from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration.grafana import exceptions

HEADERS = {"Accept": "application/json",
           "Content-Type": "application/json"
           }


''' Create Datasource '''


def _post_datasource(datasource_json):

    if utils.port_open(NS.conf.grafana_port, NS.conf.grafana_host):
        resp = post("http://{}:{}/api/datasources"
                    .format(NS.conf.grafana_host,
                            NS.conf.grafana_port),
                    headers=HEADERS,
                    auth=NS.conf.credentials,
                    data=datasource_json)

    else:
        raise exceptions.ConnectionFailedException

    return resp


def create_datasource():

    try:
        config = NS.conf
        url = "http://" + str(config.datasource_host) + ":" \
            + str(config.datasource_port)
        datasource_json = {'name': config.datasource_name,
                           'type': config.datasource_type,
                           'url': url,
                           'access': config.access,
                           'basicAuth': config.basicAuth,
                           'isDefault': config.isDefault}
        response = _post_datasource(json.dumps(datasource_json))
        return response

    except exceptions.ConnectionFailedException:
        traceback.print_stack()
        raise exceptions.ConnectionFailedException

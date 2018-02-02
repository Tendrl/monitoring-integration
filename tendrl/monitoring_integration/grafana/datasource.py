import json
import maps
import traceback

from requests import post

from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import utils

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}


def _post_datasource(datasource_json):
    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        resp = post("http://{}:{}/api/datasources"
                    .format(config.grafana_host,
                            config.grafana_port),
                    headers=HEADERS,
                    auth=config.credentials,
                    data=datasource_json)

    else:
        raise exceptions.ConnectionFailedException

    return resp


def create_datasource():
    try:
        config = maps.NamedDict(NS.config.data)
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
        logger.log("info", NS.get("publisher_id", None),
                   {'message': str(traceback.print_stack())})
        raise exceptions.ConnectionFailedException

import json
import maps
import traceback


from requests import get
from requests import post
from requests import put

from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import constants
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import utils


''' Create Datasource '''


def _post_datasource(datasource_json):
    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        resp = post(
            "http://{}:{}/api/datasources".format(
                config.grafana_host,
                config.grafana_port
            ),
            headers=constants.HEADERS,
            auth=config.credentials,
            data=datasource_json
        )

    else:
        raise exceptions.ConnectionFailedException

    return resp


def form_datasource_json():
    config = maps.NamedDict(NS.config.data)
    url = "http://" + str(config.datasource_host) + ":" \
        + str(config.datasource_port)
    datasource_json = (
        {'name': config.datasource_name,
         'type': config.datasource_type,
         'url': url,
         'access': config.access,
         'basicAuth': config.basicAuth,
         'isDefault': config.isDefault
         }
    )
    return datasource_json


def create_datasource():

    try:
        datasource_json = form_datasource_json()
        response = _post_datasource(json.dumps(datasource_json))
        return response
    except exceptions.ConnectionFailedException:
        logger.log("error", NS.get("publisher_id", None),
                   {'message': str(traceback.print_stack())})
        raise exceptions.ConnectionFailedException


def get_data_source():
    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        resp = get(
            "http://{}:{}/api/datasources/id/{}".format(
                config.grafana_host,
                config.grafana_port,
                config.datasource_name
            ),
            auth=config.credentials
        )

    else:
        raise exceptions.ConnectionFailedException

    return resp


def update_datasource(id):
    try:
        config = maps.NamedDict(NS.config.data)
        datasource_json = form_datasource_json()
        datasource_str = json.dumps(datasource_json)
        if utils.port_open(config.grafana_port, config.grafana_host):
            response = put(
                "http://{}:{}/api/datasources/{}".format(
                    config.grafana_host,
                    config.grafana_port,
                    id
                ),
                headers=constants.HEADERS,
                auth=config.credentials,
                data=datasource_str
            )
        else:
            exceptions.ConnectionFailedException
        return response

    except exceptions.ConnectionFailedException:
        logger.log("error", NS.get("publisher_id", None),
                   {'message': str(traceback.print_stack())})
        raise exceptions.ConnectionFailedException

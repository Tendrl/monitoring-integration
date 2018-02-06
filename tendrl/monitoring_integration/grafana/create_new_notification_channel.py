import json
import maps
import requests

from tendrl.monitoring_integration.grafana import constants
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import utils


def create_notification_channel(
    channel_name="test_notification_channel",
    host=constants.GRAFANA_IP,
    port=constants.GRAFANA_PORT
):
    url = "http://%s:%s/grafana_callback" % (
        str(host),
        str(port)
    )
    channel_details = json.dumps(
        {
            "name": channel_name,
            "type": "webhook",
            "isDefault": True,
            "settings": {
                "httpMethod": constants.HTTP_METHOD_POST,
                "uploadImage": "False",
                "url": url
            }
        }
    )

    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        response = requests.post(
            "http://{}:{}/api/alert-notifications".format(
                config.grafana_host,
                config.grafana_port
            ),
            headers=constants.HEADERS,
            auth=config.credentials,
            data=channel_details
        )
        return response
    else:
        raise exceptions.ConnectionFailedException

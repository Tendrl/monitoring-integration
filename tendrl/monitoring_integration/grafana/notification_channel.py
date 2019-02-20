import json
import maps
from requests import post
import socket

from tendrl.monitoring_integration.grafana import constants
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import utils

NOTIFICATION_CHANNEL = "tendrl_notification_channel"
PORT = 8789


def create_notification_channel():
    ip = socket.gethostbyname(socket.gethostname())
    url = "http://" + str(ip) + \
          ":" + str(PORT) + "/grafana_callback"
    channel_details = json.dumps({"name": NOTIFICATION_CHANNEL,
                                  "type": "webhook",
                                  "isDefault": True,
                                  "settings": {"httpMethod": "POST",
                                               "uploadImage": "False",
                                               "url": url}
                                  })

    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        response = post("http://{}:{}/api/alert-notifications"
                        .format(config.grafana_host, config.grafana_port),
                        headers=constants.HEADERS,
                        auth=config.credentials,
                        data=channel_details)

        return response
    else:
        raise exceptions.ConnectionFailedException

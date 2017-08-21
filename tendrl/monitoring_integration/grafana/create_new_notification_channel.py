import __builtin__
import json


from requests import post
import maps


from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration.grafana import exceptions


HEADERS = {"Accept": "application/json",
           "Content-Type": "application/json"
           }


def create_notification_channel(channel_name = "test_notification_channel",
                                host="127.0.0.1", port="8789"):

    url = "http://" + str(host)+ ":" + str(port) + "/grafana_callback"
    channel_details = json.dumps({"name": channel_name,
     "type":  "webhook",
     "isDefault": True,
     "settings": {
        "httpMethod": "POST",
        "uploadImage": "False",
        "url": url
       }
    })

    config = maps.NamedDict(NS.config.data)
    if utils.port_open(config.grafana_port, config.grafana_host):
        response = post("http://{}:{}/api/alert-notifications"
                       .format(config.grafana_host,
                               config.grafana_port),
                       headers=HEADERS,
                       auth=config.credentials,
                       data=channel_details)

        return response
    else:
        raise exceptions.ConnectionFailedException


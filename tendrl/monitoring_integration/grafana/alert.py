import maps

from requests import get
from tendrl.monitoring_integration.grafana import utils


def get_alert(alert_id):
    config = maps.NamedDict(NS.config.data)
    if utils.port_open(
        config.grafana_port,
        config.grafana_host
    ):
        resp = get("http://{0}:{1}/api/alerts/"
                   "{2}".format(config.grafana_host,
                                  config.grafana_port,
                                  alert_id),
                   auth=config.credentials)
    else:
        raise exceptions.ConnectionFailedException
    return resp.json()

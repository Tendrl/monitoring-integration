import maps

from requests import get
from requests.exceptions import ConnectionError
from requests.exceptions import RequestException
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import utils


def get_alert(alert_id):
    config = NS.config.data
    if utils.port_open(
        config["grafana_port"],
        config["grafana_host"]
    ):
        try:
            resp = get("http://{0}:{1}/api/alerts/"
                       "{2}".format(config["grafana_host"],
                                    config["grafana_port"],
                                    alert_id),
                       auth=config["credentials"])
        except(ConnectionError, RequestException) as ex:
            logger.log(
                "error",
                NS.publisher_id,
                {
                    "message": 'Unable to fetch alert from grafana ' + \
                    'rule id: %s' % alert_id
                }
            )
            raise ex
    else:
        logger.log(
            "error",
            NS.publisher_id,
            {
                "message": 'grafana connection error'
            }
        )
        raise exceptions.ConnectionFailedException
    return resp.json()

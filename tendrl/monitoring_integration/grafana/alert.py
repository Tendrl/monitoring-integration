import json

from requests.exceptions import ConnectionError
from requests.exceptions import RequestException
from requests import get

from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import grafana_org_utils
from tendrl.monitoring_integration.grafana import utils


def connect(alert_id, config):
    resp = get(
        "http://{0}:{1}/api/alerts/{2}".format(
            config["grafana_host"],
            config["grafana_port"],
            alert_id
        ),
        auth=config["credentials"])
    return resp


def switch_context(org_name):
    alert_org_id = grafana_org_utils.get_org_id(
        org_name
    )
    switched = grafana_org_utils.switch_context(json.loads(
        alert_org_id)["id"]
    )
    return switched


def get_alert(alert_id):
    config = NS.config.data
    if utils.port_open(
        config["grafana_port"],
        config["grafana_host"]
    ):
        try:
            resp = connect(alert_id, config)
            if "message" in resp.json():
                if resp.json()['message'] == (
                    'You are not allowed to edit/view alert'
                ):
                    # retry with swith context
                    if switch_context("Alert_dashboard"):
                        resp = connect(alert_id, config)
                        # switch context again to main org
                        switch_context("Main Org.")
        except(ConnectionError, RequestException) as ex:
            logger.log(
                "error",
                NS.publisher_id,
                {
                    "message": 'Unable to fetch alert from grafana ' +
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

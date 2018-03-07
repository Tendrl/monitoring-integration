import etcd
import json
from requests import exceptions as req_excep

from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import constants
from tendrl.monitoring_integration.grafana import \
    datasource
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import grafana_org_utils
from tendrl.monitoring_integration.grafana import \
    notification_channel


GRAFANA_AUTH_KEY = "grafana_auth_key"
GRAFANA_USER = "Admin"


def create():
    try:
        org_id = create_organization()
        if grafana_org_utils.switch_context(org_id):
            key = create_auth_key()
            NS.config.data["org_id"] = org_id
            NS.config.data["grafana_auth_key"] = key
            NS.monitoring.objects.AlertOrganization(
                org_name=constants.ALERT_ORG,
                org_id=org_id,
                auth_key=key
            ).save()
            # create datasource in alert org
            datasource.create()
            # Create notification medium
            notification_channel.create_notification_channel()
            # context swith to main org
            main_org_id = grafana_org_utils.get_org_id(
                constants.MAIN_ORG
            )
            if main_org_id:
                grafana_org_utils.switch_context(
                    json.loads(main_org_id)["id"]
                )
        else:
            msg = "Could not switch context for Alert organization"
            logger.log("debug", NS.get("publisher_id", None),
                       {'message': msg})
    except(
        KeyError,
        AttributeError,
        req_excep.ConnectionError,
        TypeError,
        req_excep.RequestException,
        etcd.EtcdException,
        exceptions.ConnectionFailedException
    ) as ex:
        msg = "Unable to create alert organization.err:%s" % ex
        logger.log("debug", NS.get("publisher_id", None),
                   {'message': msg})


def create_organization():
    # Check organization is already exist
    resp = grafana_org_utils.get_org_id(constants.ALERT_ORG)
    resp = json.loads(resp)
    if "id" in resp:
        org_id = resp['id']
        msg = ("alert organization with name %s " +
               "is already exist") % constants.ALERT_ORG
        logger.log("debug", NS.get("publisher_id", None),
                   {'message': msg})
    elif "message" in resp and resp["message"] == \
            "Organization not found":
        # Create alert organization
        org_id = grafana_org_utils.create_org(constants.ALERT_ORG)
        msg = ("alert organization %s created " +
               "successfully") % constants.ALERT_ORG
        logger.log("debug", NS.get("publisher_id", None),
                   {'message': msg})
    else:
        org_id = None
        msg = "Unable to create alert organization %s " % constants.ALERT_ORG
        logger.log("debug", NS.get("publisher_id", None),
                   {'message': msg})
    return org_id


def create_auth_key():
    # Check auth key is already exist
    resp = grafana_org_utils.get_auth_keys()
    if isinstance(resp, list):
        flag = False
        for grafana_key in resp:
            if grafana_key['name'] == GRAFANA_AUTH_KEY and \
                    grafana_key['role'] == GRAFANA_USER:
                flag = True
                break
        if not flag:
            # Create authoriztion key
            key = grafana_org_utils.create_api_token(
                GRAFANA_AUTH_KEY, GRAFANA_USER
            )
            msg = ("Grafana authentication key for user %s " +
                   "is created successfully") % GRAFANA_USER
            logger.log("debug", NS.get("publisher_id", None),
                       {'message': msg})
        else:
            alert_org = NS.monitoring.objects.AlertOrganization().load()
            key = alert_org.auth_key
            msg = ("Grafana authentication key for user %s " +
                   "is already exist") % GRAFANA_USER
            logger.log("debug", NS.get("publisher_id", None),
                       {'message': msg})
    else:
        msg = ("Unable to create grafana authentication key " +
               "for user %s") % GRAFANA_USER
        logger.log("debug", NS.get("publisher_id", None),
                   {'message': msg})
        key = None
    return key

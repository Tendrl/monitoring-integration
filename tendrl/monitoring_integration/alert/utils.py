import pkgutil

from etcd import EtcdKeyNotFound
from subprocess import CalledProcessError
from subprocess import check_output
from tendrl.commons.objects.alert import Alert
from tendrl.commons.utils import etcd_utils
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.alert import constants
from tendrl.monitoring_integration.alert.exceptions import AlertNotFound
from tendrl.monitoring_integration.alert.exceptions import Unauthorized
from tendrl.monitoring_integration.alert.exceptions import NodeNotFound
from tendrl.monitoring_integration.grafana import alert


def list_modules_in_package_path(package_path, prefix):
    modules = []
    path_to_walk = [(package_path, prefix)]
    while len(path_to_walk) > 0:
        curr_path, curr_prefix = path_to_walk.pop()
        for importer, name, ispkg in pkgutil.walk_packages(
            path=[curr_path]
        ):
            if ispkg:
                path_to_walk.append(
                    (
                        '%s/%s/' % (curr_path, name),
                        '%s.%s' % (curr_prefix, name)
                    )
                )
            else:
                modules.append((name, '%s.%s' % (curr_prefix, name)))
    return modules


def get_alert_info(alert_id):
    alert_json  = alert.get_alert(alert_id)
    if "message" in alert_json:
        if alert_json["message"] == "Alert not found":
            logger.log(
                "error",
                NS.publisher_id,
                {
                    "message": "Alert with alert id %s not "
                    "found in grafana" % alert_id
                }
            )
            raise AlertNotFound
        elif alert_json["message"] == "Unauthorized":
            logger.log(
                "error",
                NS.publisher_id,
                {
                    "message": "Authorization denied while "
                    "fetching alert information for alert %s" % alert_id
                }
            )
            raise Unauthorized
    return alert_json


def find_current_value(eval_data):
    # ok alert not have cur_value
    cur_value = constants.NOT_AVAILABLE
    if 'evalMatches' in eval_data:
        # Getting current value
        cur_value = eval_data['evalMatches'][0]['value']
    return cur_value


def find_alert_target(conditions):
    target = None
    if "targetFull" in conditions[0]['query']['model']:
        target  = conditions[0]['query']['model']["targetFull"]
    else:
        target  = conditions[0]['query']['model']["target"]
    return target


def find_warning_max(param):
    return param[0]


def find_grafana_pid():
    try:
        return check_output(
            ["pidof", "grafana-server"]).strip()
    except CalledProcessError as ex:
        logger.log(
            "error",
            NS.publisher_id,
            {
                "message": "unable to find grafana pid" 
            }
        )
        raise ex


def find_node_id(cluster_id, fqdn):
    try:
        nodes = etcd_utils.read(
            "clusters/%s/nodes" % cluster_id
        )
        for node in nodes.leaves:
            key = node.key + "/NodeContext/fqdn"
            if fqdn == etcd_utils.read(key).value:
                return node.key.split('/')[-1]
        raise NodeNotFound
    except (EtcdKeyNotFound, NodeNotFound) as ex:
        if type(ex) != etcd.EtcdKeyNotFound:
            logger.log(
                "error",
                NS.publisher_id,
                {
                    "message": "Failed to fetch fqdn for node %s" %
                    node_id
                }
            )
        else:
            logger.log(
            "error",
            NS.publisher_id,
            {
                "message": "Node with fqdn %s not found "
                "in cluster %s" % (fqdn, cluster_id)
            }
        )   
        raise ex

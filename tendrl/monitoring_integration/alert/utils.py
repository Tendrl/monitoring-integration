import pkgutil
import re

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
from tendrl.monitoring_integration.objects.alert_types import AlertTypes


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
    alert_json = alert.get_alert(alert_id)
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
    cur_value = None
    if 'evalMatches' in eval_data and eval_data['evalMatches']:
        # Getting current value
        cur_value = str(eval_data['evalMatches'][0]['value'])
    return cur_value


def find_volume_id(vol_name, integration_id):
    try:
        volumes = etcd_utils.read(
            "clusters/%s/Volumes" % integration_id
        )
        for volume in volumes.leaves:
            key = volume.key + "/name"
            name = etcd_utils.read(key).value
            if vol_name == name:
                return volume.key.split("/")[-1]
    except (EtcdKeyNotFound) as ex:
        logger.log(
            "error",
            NS.publisher_id,
            {
                "message": "Failed to fetch volume id for volume name %s" %
                vol_name
            }
        )
        raise ex


def find_alert_target(conditions):
    target = None
    if "targetFull" in conditions[0]['query']['model']:
        target = conditions[0]['query']['model']["targetFull"]
    else:
        target = conditions[0]['query']['model']["target"]
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


def find_node_id(integration_id, fqdn):
    try:
        nodes = etcd_utils.read(
            "clusters/%s/nodes" % integration_id
        )
        for node in nodes.leaves:
            node_id = node.key.split('/')[-1]
            node_context = NS.tendrl.objects.ClusterNodeContext()
            # formating value here because render populate integration_id
            # from namespace
            node_context.value = node_context.value.format(
                integration_id, node_id
            )
            if fqdn == node_context.load().fqdn:
                return node_id
        raise NodeNotFound
    except (EtcdKeyNotFound, NodeNotFound) as ex:
        if type(ex) != EtcdKeyNotFound:
            logger.log(
                "error",
                NS.publisher_id,
                {
                    "message": "Failed to fetch fqdn for node %s" %
                    fqdn
                }
            )
        else:
            logger.log(
                "error",
                NS.publisher_id,
                {
                    "message": "Node with fqdn %s not found "
                    "in cluster %s" % (fqdn, integration_id)
                }
            )
        raise ex


def find_cluster_name(integration_id):
    try:
        cluster_name = NS.tendrl.objects.ClusterTendrlContext(
            integration_id=integration_id).load().cluster_name
        return cluster_name
    except (EtcdKeyNotFound) as ex:
        logger.log(
            "error",
            NS.publisher_id,
            {
                "message": "Failed to fetch cluster name for id %s" %
                integration_id
            }
        )
        raise ex


def find_alert_types(new_alert_types):
    try:
        for alert_classification in new_alert_types:
            types = new_alert_types[alert_classification]
            alert_types = AlertTypes(
                classification=alert_classification
            ).load()
            if alert_types.types:
                types = list(set().union(
                    types, alert_types.types))
            AlertTypes(
                classification=alert_classification,
                types=types
            ).save()
    except (EtcdKeyNotFound) as ex:
        logger.log(
            "error",
            NS.publisher_id,
            {
                "message": "Failed to fetch alert types %s" %
                new_alert_types[alert_classification]
            }
        )
        raise ex


def parse_target(target, template):
    regex = re.sub(r'{(.+?)}', r'(?P<\1>.+?)', template)
    values = list(re.search(regex, target).groups())
    keys = re.findall(r'{(.+?)}', template)
    _dict = dict(zip(keys, values))
    return _dict

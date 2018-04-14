import pkgutil
import re

from etcd import EtcdKeyNotFound
from subprocess import CalledProcessError
from subprocess import check_output

from tendrl.commons.utils import etcd_utils
from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.alert.exceptions import AlertNotFound
from tendrl.monitoring_integration.alert.exceptions import PermissionDenied
from tendrl.monitoring_integration.alert.exceptions import Unauthorized
from tendrl.monitoring_integration.grafana import alert_utils


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
    alert_json = alert_utils.get_alert(alert_id)
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
        elif alert_json["message"] == "You are not allowed to edit/view alert":
            logger.log(
                "error",
                NS.publisher_id,
                {
                    "message": "Unable to fetch alert from grafana"
                    " %s err: %s" % (alert_id, alert_json["message"])
                }
            )
            raise PermissionDenied
    return alert_json


def find_current_value(eval_data):
    # ok alert not have cur_value
    cur_value = None
    if 'evalMatches' in eval_data and eval_data['evalMatches']:
        # Getting current value
        cur_value = str(round(eval_data['evalMatches'][0]['value'], 2))
    return cur_value


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
    _cluster_node_ids = etcd_utils.read(
        "/clusters/%s/nodes" % integration_id
    )
    for _node_id in _cluster_node_ids.leaves:
        _cnc = NS.tendrl.objects.ClusterNodeContext(
            integration_id=integration_id,
            node_id=_node_id.key.split('/')[-1]
        ).load()
        if _cnc.fqdn == fqdn:
            return _cnc.node_id


def find_cluster_name(integration_id):
    try:
        cluster_name = NS.tendrl.objects.ClusterTendrlContext(
            integration_id=integration_id).load().cluster_name
        return cluster_name
    except EtcdKeyNotFound as ex:
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
            alert_types = NS.monitoring.objects.AlertTypes(
                classification=alert_classification
            ).load()
            if alert_types.types:
                types = list(set().union(
                    types, alert_types.types))
            NS.monitoring.objects.AlertTypes(
                classification=alert_classification,
                types=types
            ).save()
    except EtcdKeyNotFound as ex:
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


def find_volume_name(integration_id, hostname, brick_path):
    _brick = NS.tendrl.objects.GlusterBrick(
        integration_id=integration_id,
        fqdn=hostname,
        brick_dir=brick_path
    ).load()
    if _brick:
        return _brick.vol_name
    else:
        return None


def find_cluster_short_name(integration_id):
    cluster = NS.tendrl.objects.Cluster(
        integration_id=integration_id
    ).load()
    if cluster:
        return cluster.short_name
    else:
        return None

import json
from mock import patch
import os

from tendrl.monitoring_integration.alert.handlers.cluster.gluster_handler \
    import brick_utilization_handler
from tendrl.monitoring_integration.alert import utils
from tendrl.monitoring_integration.tests import test_init


@patch.object(utils, "find_node_id")
@patch.object(utils, "find_grafana_pid")
@patch.object(utils, "find_cluster_name")
@patch.object(utils, "find_volume_name")
def test_brick_handler(vol_name, cluster_name, pid, node_id):
    vol_name.return_value = "vol1"
    node_id.return_value = "1"
    pid.return_value = "123"
    cluster_name.return_value = "c1"
    test_init.init()
    obj = brick_utilization_handler.BrickHandler()
    path = os.path.join(os.path.dirname(__file__),
                        "brick_alert_info.json")
    alert = json.load(open(path))
    result = obj.format_alert(alert)
    condition = {'significance': 'HIGH',
                 'alert_type': 'UTILIZATION',
                 'node_id': '1',
                 'resource': 'brick_utilization',
                 'time_stamp': u'2018-02-07T17:24:16+05:30',
                 'alert_id': None,
                 'current_value': None,
                 'tags': {'plugin_instance': u'tendrl.clusters.'
                          '7616f2a4-6502-4222-85bb-c5aff4eef15d.'
                          'nodes.dhcp122-234.bricks.|gluster|brick1'
                          '.utilization.percent-percent_bytes',
                          'fqdn': u'dhcp122-234',
                          'brick_path': u'|gluster|brick1',
                          'cluster_name': 'c1',
                          'integration_id': u'7616f2a4-6502-4222-85bb'
                          '-c5aff4eef15d',
                          'warning_max': 75,
                          'message': u'Brick utilization of dhcp122-234'
                          ':|gluster|brick1 under volume vol1 in cluster '
                          '7616f2a4-6502-4222-85bb-c5aff4eef15d is back '
                          'normal',
                          'volume_name': 'vol1'
                          },
                 'source': 'GRAFANA',
                 'severity': 'INFO',
                 'pid': '123'
                 }
    if not result == condition:
        raise AssertionError()
    obj = brick_utilization_handler.BrickHandler()
    path = os.path.join(os.path.dirname(__file__),
                        "brick_alert_error.json")
    alert = json.load(open(path))
    result = obj.format_alert(alert)
    condition = {'severity': 'WARNING',
                 'significance': 'HIGH',
                 'alert_type': 'UTILIZATION',
                 'alert_id': None,
                 'time_stamp': u'2018-02-12T13:13:03+05:30',
                 'tags': {'plugin_instance': u'tendrl.clusters.7616f2a4'
                          '-6502-4222-85bb-c5aff4eef15d.nodes.dhcp122-'
                          '234.bricks.|gluster|brick1.utilization.'
                          'percent-percent_bytes',
                          'fqdn': u'dhcp122-234',
                          'message': u'Brick utilization of dhcp122-234:|'
                          'gluster|brick1 under volume vol1 in cluster '
                          '7616f2a4-6502-4222-85bb-c5aff4eef15d is 20.75 % '
                          'which is above WARNING threshold (17 %)',
                          'integration_id': u'7616f2a4-6502-4222-85bb-'
                          'c5aff4eef15d',
                          'cluster_name': 'c1',
                          'brick_path': u'|gluster|brick1',
                          'warning_max': 17,
                          'volume_name': 'vol1'
                          },
                 'pid': '123',
                 'node_id': '1',
                 'resource': 'brick_utilization',
                 'source': 'GRAFANA',
                 'current_value': '20.75'
                 }
    if not result == condition:
        raise AssertionError()

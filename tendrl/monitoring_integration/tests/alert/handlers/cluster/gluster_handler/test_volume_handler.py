import json
from mock import patch
import os

from tendrl.monitoring_integration.alert.handlers.cluster.gluster_handler \
    import volume_utilization_handler
from tendrl.monitoring_integration.alert import utils
from tendrl.monitoring_integration.tests import test_init


@patch.object(utils, "find_cluster_short_name")
@patch.object(utils, "find_grafana_pid")
@patch.object(utils, "find_cluster_name")
def test_volume_handler(cluster_name, pid, short_name):
    short_name.return_value = '7616f2a4-6502-4222-85bb-c5aff4eef15d'
    pid.return_value = "123"
    cluster_name.return_value = "c1"
    test_init.init()
    obj = volume_utilization_handler.VolumeHandler()
    path = os.path.join(os.path.dirname(__file__),
                        "volume_alert_info.json")
    alert = json.load(open(path))
    result = obj.format_alert(alert)
    condition = {'severity': 'INFO',
                 'source': 'GRAFANA',
                 'pid': '123',
                 'time_stamp': u'2018-02-07T17:30:08+05:30',
                 'alert_id': None,
                 'resource': 'volume_utilization',
                 'significance': 'HIGH',
                 'current_value': None,
                 'node_id': None,
                 'alert_type': 'UTILIZATION',
                 'tags': {'cluster_name': 'c1',
                          'message': u'Volume utilization on '
                          'V1 in 7616f2a4-6502-4222-'
                          '85bb-c5aff4eef15d back to normal',
                          'warning_max': 75,
                          'volume_name': u'V1',
                          'integration_id': u'7616f2a4-6502-4222'
                          '-85bb-c5aff4eef15d',
                          'cluster_short_name': '7616f2a4-6502-4222-'
                          '85bb-c5aff4eef15d',
                          'plugin_instance': u'tendrl.names.'
                          '7616f2a4-6502-4222-85bb-c5aff4eef15d.'
                          'volumes.V1.pcnt_used'
                          }
                 }
    if not result == condition:
        raise AssertionError()
    path = os.path.join(os.path.dirname(__file__),
                        "volume_alert_error.json")
    alert = json.load(open(path))
    result = obj.format_alert(alert)
    condition = {'time_stamp': u'2018-02-12T13:36:25+05:30',
                 'significance': 'HIGH',
                 'alert_type': 'UTILIZATION',
                 'node_id': None,
                 'severity': 'WARNING',
                 'resource': 'volume_utilization',
                 'pid': '123',
                 'tags': {'cluster_name': 'c1',
                          'volume_name': u'V1',
                          'cluster_short_name': '7616f2a4-6502-4222-'
                          '85bb-c5aff4eef15d',
                          'plugin_instance': u'tendrl.names.'
                          '7616f2a4-6502-4222-85bb-c5aff4eef15d.'
                          'volumes.V1.pcnt_used',
                          'warning_max': 14,
                          'integration_id': u'7616f2a4-6502-4222'
                          '-85bb-c5aff4eef15d',
                          'message': u'Volume utilization on V1 in'
                          ' 7616f2a4-6502-4222-85bb-c5aff4eef1'
                          '5d at 20.86 % and nearing full capacity'
                          },
                 'source': 'GRAFANA',
                 'current_value': '20.86',
                 'alert_id': None
                 }
    if not result == condition:
        raise AssertionError()

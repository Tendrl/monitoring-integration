import json
from mock import patch
import os

from tendrl.monitoring_integration.alert.handlers.node import \
    cpu_handler
from tendrl.monitoring_integration.alert import utils
from tendrl.monitoring_integration.tests import test_init


@patch.object(utils, "find_node_id")
@patch.object(utils, "find_grafana_pid")
def test_cpu_handler(pid, node_id):
    node_id.return_value = "1"
    pid.return_value = "123"
    test_init.init()
    obj = cpu_handler.CpuHandler()
    path = os.path.join(os.path.dirname(__file__),
                        "cpu_alert_info.json")
    alert = json.load(open(path))
    result = obj.format_alert(alert)
    condition = {'alert_id': None,
                 'alert_type': 'UTILIZATION',
                 'severity': 'INFO',
                 'significance': 'HIGH',
                 'node_id': '1',
                 'current_value': None,
                 'source': 'GRAFANA',
                 'resource': 'cpu_utilization',
                 'pid': '123',
                 'time_stamp': u'2018-02-07T17:28:05+05:30',
                 'tags': {'warning_max': 80,
                          'fqdn': u'dhcp122-234',
                          'message': u'Cpu utilization on '
                          'dhcp122-234 in '
                          '7616f2a4-6502-4222-'
                          '85bb-c5aff4eef15d back to normal',
                          'integration_id': '7616f2a4-6502-4222-'
                          '85bb-c5aff4eef15d'
                          }
                 }
    if not result == condition:
        raise AssertionError()
    path = os.path.join(os.path.dirname(__file__),
                        "cpu_alert_error.json")
    alert = json.load(open(path))
    result = obj.format_alert(alert)
    condition = {'pid': '123',
                 'tags': {'fqdn': u'dhcp122-234',
                          'warning_max': 1,
                          'message': u'Cpu utilization on '
                          'dhcp122-234 in 7616f2a4-6502-4222-'
                          '85bb-c5aff4eef15d at 2.61 % and '
                          'running out of cpu',
                          'integration_id': '7616f2a4-6502-4222-'
                          '85bb-c5aff4eef15d'
                          },
                 'alert_id': None,
                 'source': 'GRAFANA',
                 'current_value': '2.61',
                 'significance': 'HIGH',
                 'time_stamp': u'2018-02-12T10:53:03+05:30',
                 'node_id': '1',
                 'alert_type': 'UTILIZATION',
                 'severity': 'WARNING',
                 'resource': 'cpu_utilization'
                 }
    if not result == condition:
        raise AssertionError()

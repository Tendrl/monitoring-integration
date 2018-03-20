import json
from mock import patch
import os

from tendrl.monitoring_integration.alert.handlers.node import \
    memory_handler
from tendrl.monitoring_integration.alert import utils
from tendrl.monitoring_integration.tests import test_init


@patch.object(utils, "find_node_id")
@patch.object(utils, "find_grafana_pid")
def test_memory_handler(pid, node_id):
    node_id.return_value = "1"
    pid.return_value = "123"
    test_init.init()
    obj = memory_handler.MemoryHandler()
    path = os.path.join(os.path.dirname(__file__),
                        "memory_alert_info.json")
    alert = json.load(open(path))
    result = obj.format_alert(alert)
    condition = {'pid': '123',
                 'tags': {'warning_max': 80,
                          'fqdn': u'dhcp122-234',
                          'message': u'Memory utilization of '
                          'node dhcp122-234 is back to normal',
                          'integration_id': '7616f2a4-6502-4222-85bb-'
                          'c5aff4eef15d'
                          },
                 'current_value': None,
                 'source': 'GRAFANA',
                 'alert_id': None,
                 'alert_type': 'UTILIZATION',
                 'time_stamp': u'2018-02-07T17:29:01+05:30',
                 'significance': 'HIGH',
                 'node_id': '1',
                 'resource': 'memory_utilization',
                 'severity': 'INFO',
                 }
    if not result == condition:
        raise AssertionError()
    path = os.path.join(os.path.dirname(__file__),
                        "memory_alert_error.json")
    alert = json.load(open(path))
    result = obj.format_alert(alert)
    condition = {'resource': 'memory_utilization',
                 'source': 'GRAFANA',
                 'significance': 'HIGH',
                 'alert_type': 'UTILIZATION',
                 'severity': 'WARNING',
                 'current_value': '29.47',
                 'node_id': '1',
                 'tags': {'fqdn': u'dhcp122-234',
                          'message': u'Memory utilization of '
                          'node dhcp122-234 '
                          'is 29.47 % which is above the WARNING '
                          'threshold (23 %).',
                          'warning_max': 23,
                          'integration_id': '7616f2a4-6502-4222-85bb-'
                          'c5aff4eef15d'
                          },
                 'time_stamp': u'2018-02-12T11:30:19+05:30',
                 'alert_id': None,
                 'pid': '123'
                 }
    if not result == condition:
        raise AssertionError()

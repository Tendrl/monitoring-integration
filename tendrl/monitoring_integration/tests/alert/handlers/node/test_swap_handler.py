import json
from mock import patch
import os

from tendrl.monitoring_integration.alert.handlers.node import \
    swap_handler
from tendrl.monitoring_integration.alert import utils
from tendrl.monitoring_integration.tests import test_init


@patch.object(utils, "find_node_id")
@patch.object(utils, "find_grafana_pid")
def test_swap_handler(pid, node_id):
    node_id.return_value = "1"
    pid.return_value = "123"
    test_init.init()
    obj = swap_handler.SwapHandler()
    path = os.path.join(os.path.dirname(__file__),
                        "swap_alert_info.json")
    alert = json.load(open(path))
    result = obj.format_alert(alert)
    condition = {'alert_id': None,
                 'alert_type': 'UTILIZATION',
                 'severity': 'INFO',
                 'time_stamp': u'2018-02-07T17:40:02+05:30',
                 'pid': '123',
                 'tags': {'warning_max': 50,
                          'message': u'Swap utilization on node '
                          'dhcp122-234 in 7616f2a4-6502-4222-85bb'
                          '-c5aff4eef15d back to normal',
                          'fqdn': u'dhcp122-234',
                          'integration_id': '7616f2a4-6502-4222-85bb-'
                          'c5aff4eef15d'
                          },
                 'resource': 'swap_utilization',
                 'node_id': '1',
                 'current_value': None,
                 'source': 'GRAFANA',
                 'significance': 'HIGH'
                 }
    if not result == condition:
        raise AssertionError()
    path = os.path.join(os.path.dirname(__file__),
                        "swap_alert_error.json")
    alert = json.load(open(path))
    result = obj.format_alert(alert)
    condition = {'alert_type': 'UTILIZATION',
                 'alert_id': None,
                 'resource': 'swap_utilization',
                 'time_stamp': u'2018-02-12T11:16:23+05:30',
                 'pid': '123',
                 'tags': {'warning_max': 70,
                          'message': u'Swap utilization on node '
                          'dhcp122-234 in 7616f2a4-6502-4222-85bb-'
                          'c5aff4eef15d at 80.0 % and running out of '
                          'swap space',
                          'fqdn': u'dhcp122-234',
                          'integration_id': '7616f2a4-6502-4222-85bb-'
                          'c5aff4eef15d'
                          },
                 'source': 'GRAFANA',
                 'significance': 'HIGH',
                 'current_value': '80.0',
                 'severity': 'WARNING',
                 'node_id': '1'
                 }
    if not result == condition:
        raise AssertionError()

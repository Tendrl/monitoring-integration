from mock import patch
import os

from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import \
    alert_dashboard
from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration.tests import test_init


@patch.object(os.path, "exists")
@patch.object(utils, "fread")
@patch.object(logger, "log")
def test_alert_dashboard(log, fread, exist):
    exist.return_value = True
    path = os.path.join(os.path.dirname(__file__),
                        "dashboard.json")
    with open(path) as f:
        fread.return_value = f.read()
    test_init.init()
    with patch.object(NS.monitoring.definitions,
                      "get_parsed_defs") as mock_defs:
        threshold = {'capacity_utilization': {'Warning': 75, 'Critical': 90}}
        mock_defs.return_value = (
            {"namespace.monitoring": {"thresholds": {"volumes": threshold}}}
        )
        resource = {'vol_id': '4ff7cf55-a6ef-4ea1-a8ea-f406803503a4',
                    'name': 'V2',
                    'sds_name': 'gluster',
                    'integration_id': 'f3a74e36-0462-4fb0-9a92-3ee9d244f8a2',
                    'resource_name': 'V2'
                    }
        resource_json = alert_dashboard.create_resource_dashboard(
            "volumes",
            resource
        )
        new_res, resource_json, panel_id = alert_dashboard.check_duplicate(
            resource_json,
            [resource],
            'volumes'
        )
        if not (panel_id == 2 and new_res == []):
            raise AssertionError
        resource['name'] = 'V3'
        resource['resource_name'] = 'V3'
        resource_json = alert_dashboard.add_panel(
            [resource],
            'volumes',
            resource_json,
            panel_id
        )
        if not len(resource_json["dashboard"]["rows"]) == 2:
            raise AssertionError

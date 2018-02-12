import maps
from mock import patch
import os

from tendrl.commons.utils import log_utils as logger
from tendrl.monitoring_integration.grafana import alert_utils
from tendrl.monitoring_integration.grafana import \
    create_alert_dashboard
from tendrl.monitoring_integration.grafana import utils


@patch.object(os.path, "exists")
@patch.object(utils, "fread")
@patch.object(alert_utils, "post_dashboard")
@patch.object(logger, "log")
def test_create_alert_dashboard(log, post, fread, exist):
    post.return_value = maps.NamedDict(status_code=200)
    exist.return_value = True
    path = os.path.join(os.path.dirname(__file__),
                        "dashboard.json")
    with open(path) as f:
        fread.return_value = f.read()
    with patch.object(NS.monitoring.definitions,
                      "get_parsed_defs") as mock_defs:
        threshold = {'capacity_utilization': {'Warning': 75}}
        mock_defs.return_value = (
            {"namespace.monitoring": {"thresholds": {"volumes": threshold}}}
        )
        create_alert_dashboard.create_resource_dashboard(
            "volumes",
            {'vol_id': u'4ff7cf55-a6ef-4ea1-a8ea-f406803503a4',
             'name': u'V2',
             'subvolume': [{'bricks': [u'dhcp122-137:_gluster_brick2'],
                            'subvolume': u'subvolume1'
                            },
                           {'bricks': [u'dhcp122-234:_gluster_brick2'],
                            'subvolume': u'subvolume2'
                            },
                           {'bricks': [u'dhcp122-3:_gluster_brick2'],
                            'subvolume': u'subvolume0'
                            }]
             },
            'gluster',
            'f3a74e36-0462-4fb0-9a92-3ee9d244f8a2'
        )
        log.assert_called_with(
            'info',
            'monitoring_integration',
            {'message': 'Alert dashboard for '
             'volumes- is created successfully'
             }
        )

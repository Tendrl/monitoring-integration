import maps
import mock
import os
import pytest

from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration.tests.test_init import init


def test_create_dashboard():
    init()
    utils.get_conf()
    with mock.patch.object(dashboard, '_post_dashboard',
                           return_value=maps.NamedDict(status_code=200)):
        dashboard_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        for dashboard_json in NS.conf.dashboards:
            ret = dashboard.create_dashboard(dashboard_json, dashboard_dir)
            assert ret.status_code == 200

    with mock.patch.object(utils, 'port_open',
                           return_value=False):
        dashboard_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        for dashboard_json in NS.conf.dashboards:
            with pytest.raises(exceptions.ConnectionFailedException):
                ret = dashboard.create_dashboard(dashboard_json, dashboard_dir)

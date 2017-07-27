import __builtin__
import os


import maps
import pytest
from mock import patch


from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.grafana import exceptions


def test_create_dashboard():
    grafana_conf = os.path.join(os.path.dirname(__file__), "fixtures",
                                "test_monitoring-integration.conf.yaml")
    config = utils.get_conf(grafana_conf)
    setattr(__builtin__, "NS", maps.NamedDict())
    setattr(NS, "conf", config)
    with patch.object(dashboard, '_post_dashboard',
                      return_value=maps.NamedDict(status_code=200)):
        dashboard_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        for dashboard_json in NS.conf.dashboards:
            ret = dashboard.create_dashboard(dashboard_json, dashboard_dir)
            assert ret.status_code == 200

    with patch.object(utils, 'port_open',
                      return_value=False):
        dashboard_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        for dashboard_json in NS.conf.dashboards:
            with pytest.raises(exceptions.ConnectionFailedException):
                ret = dashboard.create_dashboard(dashboard_json, dashboard_dir)

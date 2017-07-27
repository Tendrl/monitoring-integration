import __builtin__
import os


import maps
import pytest
from mock import patch


from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration.grafana import datasource
from tendrl.monitoring_integration.grafana import exceptions


def test_create_datasource():
    grafana_conf = os.path.join(os.path.dirname(__file__), "fixtures",
                                "test_monitoring-integration.conf.yaml")
    config = utils.get_conf(grafana_conf)
    setattr(__builtin__, "NS", maps.NamedDict())
    setattr(NS, "conf", config)
    with patch.object(datasource, '_post_datasource',
                      return_value=maps.NamedDict(status_code=200)):
        ret = datasource.create_datasource()
        assert ret.status_code == 200
    with patch.object(utils, 'port_open',
                      return_value=False):
        with pytest.raises(exceptions.ConnectionFailedException):
            ret = datasource.create_datasource()

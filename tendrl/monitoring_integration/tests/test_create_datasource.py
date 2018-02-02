import maps
import mock
import pytest

from tendrl.monitoring_integration.grafana import datasource
from tendrl.monitoring_integration.grafana import exceptions
from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration.tests.test_init import init


def test_create_datasource():
    init()
    utils.get_conf()
    with mock.patch.object(datasource, '_post_datasource',
                           return_value=maps.NamedDict(status_code=200)):
        ret = datasource.create_datasource()
        assert ret.status_code == 200
    with mock.patch.object(utils, 'port_open',
                           return_value=False):
        with pytest.raises(exceptions.ConnectionFailedException):
            ret = datasource.create_datasource()

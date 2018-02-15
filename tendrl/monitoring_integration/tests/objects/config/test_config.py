from mock import patch

from tendrl.commons import config as cmn_config
from tendrl.monitoring_integration.objects import config


@patch.object(cmn_config, "load_config")
def test_config(load_config):
    load_config.return_value = "test_monitoring"
    obj = config.Config()
    if obj.data is not "test_monitoring":
        raise AssertionError()

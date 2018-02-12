from mock import patch
import pkg_resources
from ruamel import yaml

from tendrl.monitoring_integration.objects import definition


@patch.object(yaml, "safe_load")
@patch.object(pkg_resources, "resource_string")
def test_config(resource_str, safe_load):
    resource_str.return_value = "test_monitoring"
    safe_load.return_value = {}
    obj = definition.Definition()
    assert obj.data == "test_monitoring"
    assert obj.get_parsed_defs() == {}

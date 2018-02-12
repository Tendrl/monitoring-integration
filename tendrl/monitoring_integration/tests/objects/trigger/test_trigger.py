from tendrl.monitoring_integration.objects import trigger


def test_config():
    obj = trigger.Trigger("update", "volume", "v1")
    assert obj.resource_name == "v1"
    assert obj.resource_type == "volume"
    assert obj.action == "update"

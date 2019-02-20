from tendrl.monitoring_integration.objects import trigger


def test_config():
    obj = trigger.Trigger("update", "volume", "v1")
    if obj.resource_name != "v1" and \
        obj.resource_type != "volume" and \
            obj.action != "update":
        raise AssertionError()

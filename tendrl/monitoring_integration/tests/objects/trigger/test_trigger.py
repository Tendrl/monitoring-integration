from tendrl.monitoring_integration.objects import trigger


def test_config():
    obj = trigger.Trigger("update", "volume", "v1")
    if obj.resource_name is not "v1" and \
        obj.resource_type is not "volume" and \
            obj.action is not "update":
        raise AssertionError()

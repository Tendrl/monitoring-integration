from mock import patch

from tendrl.monitoring_integration.grafana import alert
from tendrl.monitoring_integration.grafana import grafana_org_utils
from tendrl.monitoring_integration.tests import test_init


def test_connect():
    test_init.init()

    def get(url, auth):
        return 200

    alert.get = get
    resp = alert.connect(1, NS.config.data)
    assert resp == 200


@patch.object(grafana_org_utils, "get_org_id")
@patch.object(grafana_org_utils, "switch_context")
def test_switch_context(context, get_org_id):
    context.return_value = True
    get_org_id.return_value = '{"id": 1}'
    resp = alert.switch_context("test")
    assert resp is True

import mock
from mock import patch
import pytest
import threading

from tendrl.commons.manager import Manager
from tendrl.commons.objects import BaseObject
import tendrl.commons.objects.node_context as node
from tendrl.monitoring_integration.grafana import \
    alert_organization
from tendrl.monitoring_integration.grafana import dashboard
from tendrl.monitoring_integration.grafana import utils
from tendrl.monitoring_integration import manager
from tendrl.monitoring_integration.tests import test_init
from tendrl.monitoring_integration.webhook import webhook_receiver


class TimeOutException(Exception):
    pass


def wait(obj, timeout):
    raise TimeOutException


@patch.object(node.NodeContext, '_get_node_id')
@patch.object(BaseObject, "load")
@patch.object(utils, "port_open")
@patch.object(alert_organization, "create")
@patch.object(dashboard, "upload_default_dashboards")
@patch.object(webhook_receiver, "WebhookReceiver")
@patch.object(Manager, "start")
def test_main(com_start, webhook, dashboard, create,
              port, load, get_id):
    manager.monitoring_integration.MonitoringIntegrationNS = \
        test_init.init
    get_id.return_value = 1
    load.return_value = mock.MagicMock()
    webhook.return_value = mock.MagicMock()
    dashboard.return_value = True
    create.return_value = True
    port.return_value = True
    manager.TendrlNS = mock.MagicMock()
    manager.sync = mock.MagicMock()
    com_start.return_value = True
    with mock.patch.object(threading._Event, "wait", wait):
        with pytest.raises(TimeOutException):
            manager.main()

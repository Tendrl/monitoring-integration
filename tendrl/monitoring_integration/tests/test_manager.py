import maps
import mock
import threading

from tendrl.monitoring_integration import manager
from tendrl.monitoring_integration.manager import \
    MonitoringIntegrationManager
from tendrl.monitoring_integration.objects.config import \
    Config
from tendrl.monitoring_integration.objects.definition import \
    Definition


@mock.patch(
    'tendrl.monitoring_integration.grafana.webhook_receiver.'
    'WebhookReceiver.__init__',
    mock.Mock(return_value=None)
)
def test_constructor(monkeypatch):
    """Test for constructor involves if all the needed

    variables are initialized
    """

    manager = MonitoringIntegrationManager()
    assert manager._message_handler_thread is None
    assert isinstance(manager._sds_sync_thread, mock.MagicMock)


@mock.patch(
    'tendrl.monitoring_integration.manager.MonitoringIntegrationManager.start',
    mock.Mock()
)
@mock.patch(
    'tendrl.monitoring_integration.manager.MonitoringIntegrationManager.stop',
    mock.Mock()
)
@mock.patch(
    'threading.Event', mock.Mock(return_value=threading.Event())
)
@mock.patch(
    'tendrl.monitoring_integration.MonitoringIntegrationNS.__init__',
    mock.Mock(return_value=None)
)
@mock.patch(
    'tendrl.commons.TendrlNS.__init__',
    mock.Mock(return_value=None)
)
@mock.patch(
    'tendrl.commons.message.Message.__init__',
    mock.Mock(return_value=None)
)
@mock.patch(
    'tendrl.commons.utils.log_utils.log',
    mock.Mock(return_value=None)
)
@mock.patch(
    'tendrl.monitoring_integration.objects.definition.Definition.save',
    mock.Mock(return_value=None)
)
@mock.patch(
    'tendrl.monitoring_integration.objects.config.Config.save',
    mock.Mock(return_value=None)
)
@mock.patch(
    'tendrl.monitoring_integration.objects.definition.Definition.__init__',
    mock.Mock(return_value=None)
)
@mock.patch(
    'tendrl.monitoring_integration.objects.config.Config.__init__',
    mock.Mock(return_value=None)
)
@mock.patch(
    'tendrl.monitoring_integration.sync'
    '.MonitoringIntegrationSdsSyncThread.__init__',
    mock.Mock(return_value=None)
)
@mock.patch(
    'tendrl.commons.jobs.JobConsumerThread.__init__',
    mock.Mock(return_value=None)
)
@mock.patch(
    'signal.signal', mock.Mock(return_value=None)
)
def test_main(monkeypatch):
    NS.tendrl_context = mock.MagicMock()
    NS.tendrl_context.integration_id = "int-id"
    NS.message_handler_thread = mock.MagicMock()

    defs = Definition()
    defs.data = mock.MagicMock()
    cfgs = Config()
    cfgs.data = {"with_internal_profiling": False}
    setattr(NS, "monitoring", maps.NamedDict())
    NS.monitoring.definitions = defs
    NS.monitoring.config = cfgs

    t = threading.Thread(target=manager.main, kwargs={})
    t.start()
    t.join()

    assert NS.type == "monitoring"
    assert NS.publisher_id == "monitoring_integration"
    assert NS.sync_thread is not None
    assert NS.message_handler_thread is not None

    with mock.patch.object(MonitoringIntegrationManager, 'start') \
        as manager_start:
        manager_start.assert_called
    with mock.patch.object(Definition, 'save') as def_save:
        def_save.assert_called
    with mock.patch.object(Config, 'save') as conf_save:
        conf_save.assert_called

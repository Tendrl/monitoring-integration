import __builtin__
import etcd
from etcd import Client
import maps
import mock
from mock import patch

import tendrl.commons.objects.node_context as node
from tendrl.commons import TendrlNS


@patch.object(etcd, "Client")
@patch.object(Client, "read")
@patch.object(node.NodeContext, '_get_node_id')
def init(patch_get_node_id, patch_read, patch_client):
    patch_get_node_id.return_value = 1
    patch_read.return_value = etcd.Client()
    patch_client.return_value = etcd.Client()
    setattr(__builtin__, "NS", maps.NamedDict())
    setattr(NS, "_int", maps.NamedDict())
    setattr(NS, "type", "monitoring")
    setattr(NS, "publisher_id", "monitoring_integration")
    NS._int.etcd_kwargs = {
        'port': 1,
        'host': 2,
        'allow_reconnect': True}
    NS._int.client = etcd.Client(**NS._int.etcd_kwargs)
    NS["config"] = maps.NamedDict()
    NS["conf"] = maps.NamedDict()
    NS.config["data"] = maps.NamedDict()
    NS.conf["dashboards"] = []
    NS.config.data['tags'] = "test"
    NS.sync_thread = mock.MagicMock()
    NS.message_handler_thread = mock.MagicMock()
    setattr(NS.config.data, "credentials", mock.MagicMock())
    setattr(NS.config.data, "datasource_host", "127.0.0.1")
    setattr(NS.config.data, "datasource_port", "3000")
    setattr(NS.config.data, "datasource_name", "test")
    setattr(NS.config.data, "datasource_type", "test_type")
    setattr(NS.config.data, "access", "test")
    setattr(NS.config.data, "basicAuth", True)
    setattr(NS.config.data, "isDefault", True)
    tendrlNS = TendrlNS()
    return tendrlNS

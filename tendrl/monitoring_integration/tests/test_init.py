import etcd
from etcd import Client
import maps
import mock
from mock import patch

from tendrl.commons import config as cmn_config
import tendrl.commons.objects.node_context as node
from tendrl.commons import TendrlNS
from tendrl.commons.utils.central_store import utils as cs_utils


@patch.object(etcd, "Client")
@patch.object(Client, "read")
@patch.object(Client, "write")
@patch.object(cs_utils, "write")
@patch.object(cs_utils, "read")
@patch.object(cmn_config, "load_config")
@patch.object(node.NodeContext, '_get_node_id')
def init(patch_get_node_id=None,
         load_conf=None,
         util_read=None,
         util_write=None,
         patch_write=None,
         patch_read=None,
         patch_client=None
         ):
    patch_get_node_id.return_value = 1
    patch_read.return_value = etcd.Client()
    patch_write.return_value = etcd.Client()
    patch_client.return_value = etcd.Client()
    util_read.return_value = etcd.Client()
    util_write.return_value = etcd.Client()
    # creating monitoring NS
    dummy_conf = {"etcd_port": "1234",
                  "etcd_connection": "127.0.0.1"
                  }
    load_conf.return_value = dummy_conf
    TendrlNS("monitoring", "tendrl.monitoring_integration")
    # overwriting conf
    setattr(NS, "type", "monitoring")
    setattr(NS, "publisher_id", "monitoring_integration")
    NS._int.etcd_kwargs = {
        'port': 1,
        'host': 2,
        'allow_reconnect': True}
    NS["config"] = maps.NamedDict()
    NS["conf"] = maps.NamedDict()
    NS.config["data"] = maps.NamedDict()
    NS.conf["dashboards"] = []
    NS.config.data['tags'] = "test"
    setattr(NS.config.data, "credentials", mock.MagicMock())
    setattr(NS.config.data, "grafana_host", "127.0.0.1")
    setattr(NS.config.data, "grafana_port", "1234")
    setattr(NS.config.data, "datasource_host", "127.0.0.1")
    setattr(NS.config.data, "datasource_port", "234")
    setattr(NS.config.data, "datasource_name", "test")
    setattr(NS.config.data, "datasource_type", "test_type")
    setattr(NS.config.data, "access", "test")
    setattr(NS.config.data, "basicAuth", True)
    setattr(NS.config.data, "isDefault", True)
    TendrlNS()

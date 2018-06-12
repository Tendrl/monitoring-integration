import etcd
from etcd import Client
import maps
import mock
from mock import MagicMock
from mock import patch

from tendrl.commons import config as cmn_config
from tendrl.commons.objects import BaseObject
import tendrl.commons.objects.node_context as node
from tendrl.commons import TendrlNS
from tendrl.commons.utils.central_store import utils as cs_utils
from tendrl.commons.utils import etcd_utils


def init():
    with patch.object(etcd, "Client") as patch_client:
        with patch.object(Client, "read") as patch_read:
            with patch.object(Client, "write") as patch_write:
                with patch.object(cs_utils, "write") as util_write:
                    with patch.object(cs_utils, "read") as util_read:
                        with patch.object(
                            cmn_config,
                            "load_config"
                        ) as load_conf:
                            with patch.object(
                                node.NodeContext,
                                '_get_node_id'
                            ) as patch_get_node_id:
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
                                TendrlNS("monitoring",
                                         "tendrl.monitoring_integration")
                                # overwriting conf
                                setattr(NS, "type", "monitoring")
                                setattr(NS,
                                        "publisher_id",
                                        "monitoring_integration")
                                NS._int.etcd_kwargs = {
                                    'port': 1,
                                    'host': 2,
                                    'allow_reconnect': True}
                                NS["config"] = maps.NamedDict()
                                NS["conf"] = maps.NamedDict()
                                NS.config["data"] = maps.NamedDict()
                                NS.conf["dashboards"] = []
                                NS.config.data['tags'] = "test"
                                setattr(NS.config.data,
                                        "credentials",
                                        mock.MagicMock())
                                setattr(NS.config.data,
                                        "grafana_host",
                                        "127.0.0.1")
                                setattr(NS.config.data,
                                        "grafana_port",
                                        "1234")
                                setattr(NS.config.data,
                                        "datasource_host",
                                        "127.0.0.1")
                                setattr(NS.config.data,
                                        "datasource_port",
                                        "234")
                                setattr(NS.config.data,
                                        "datasource_name",
                                        "test")
                                setattr(NS.config.data,
                                        "datasource_type",
                                        "test_type")
                                setattr(NS.config.data,
                                        "access",
                                        "test")
                                setattr(NS.config.data,
                                        "basicAuth",
                                        True)
                                setattr(NS.config.data,
                                        "isDefault",
                                        True)
                                with patch.object(
                                    etcd_utils, "read"
                                ) as utils_read:
                                    utils_read.return_value = maps.NamedDict(
                                        value='{"tags":[]}'
                                    )
                                    with patch.object(
                                        BaseObject, "load"
                                    ) as node_load:
                                        node.load = MagicMock()
                                        node_load.return_value = node
                                        TendrlNS()
